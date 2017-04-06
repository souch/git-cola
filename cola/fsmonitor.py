# Copyright (c) 2008 David Aguilar
# Copyright (c) 2015 Daniel Harding
"""Provides an filesystem monitoring for Linux (via inotify) and for Windows
(via pywin32 and the ReadDirectoryChanges function)"""
from __future__ import division, absolute_import, unicode_literals

import errno
import os
import os.path
import select
from threading import Lock

from . import utils
from . import version
from .decorators import memoize

AVAILABLE = None

if utils.is_win32():
    try:
        import pywintypes
        import win32con
        import win32event
        import win32file
    except ImportError:
        pass
    else:
        AVAILABLE = 'pywin32'
elif utils.is_linux():
    try:
        from . import inotify
    except ImportError:
        pass
    else:
        AVAILABLE = 'inotify'

from qtpy import QtCore
from qtpy.QtCore import Signal

from . import core
from . import gitcfg
from . import gitcmds
from .compat import bchr
from .git import git
from .i18n import N_
from .interaction import Interaction


class _Monitor(QtCore.QObject):

    files_changed = Signal()

    def __init__(self, thread_class):
        QtCore.QObject.__init__(self)
        self._thread_class = thread_class
        self._thread = None

    def start(self):
        if self._thread_class is not None:
            assert self._thread is None
            self._thread = self._thread_class(self)
            self._thread.start()

    def stop(self):
        if self._thread_class is not None:
            assert self._thread is not None
            self._thread.stop()
            self._thread.wait()
            self._thread = None

    def refresh(self):
        if self._thread is not None:
            self._thread.refresh()


class _BaseThread(QtCore.QThread):
    #: The delay, in milliseconds, between detecting file system modification
    #: and triggering the 'files_changed' signal, to coalesce multiple
    #: modifications into a single signal.
    _NOTIFICATION_DELAY = 888

    def __init__(self, monitor):
        QtCore.QThread.__init__(self)
        self._monitor = monitor
        self._running = True
        self._use_check_ignore = version.check_git('check-ignore')
        self._force_notify = False
        self._file_paths = set()

    @property
    def _pending(self):
        return self._force_notify or self._file_paths

    def refresh(self):
        """Do any housekeeping necessary in response to repository changes."""
        pass

    def notify(self):
        """Notifies all observers"""
        do_notify = False
        if self._force_notify:
            do_notify = True
        elif self._file_paths:
            proc = core.start_command(['git', 'check-ignore', '--verbose',
                                       '--non-matching', '-z', '--stdin'])
            path_list = bchr(0).join(core.encode(path)
                                     for path in self._file_paths)
            out, err = proc.communicate(path_list)
            if proc.returncode:
                do_notify = True
            else:
                # Each output record is four fields separated by NULL
                # characters (records are also separated by NULL characters):
                # <source> <NULL> <linenum> <NULL> <pattern> <NULL> <pathname>
                # For paths which are not ignored, all fields will be empty
                # except for <pathname>.  So to see if we have any non-ignored
                # files, we simply check every fourth field to see if any of
                # them are empty.
                source_fields = out.split(bchr(0))[0:-1:4]
                do_notify = not all(source_fields)
        self._force_notify = False
        self._file_paths = set()
        if do_notify:
            self._monitor.files_changed.emit()

    @staticmethod
    def _log_enabled_message():
        msg = N_('File system change monitoring: enabled.\n')
        Interaction.safe_log(msg)


if AVAILABLE == 'inotify':

    class _InotifyThread(_BaseThread):
        _TRIGGER_MASK = (
                inotify.IN_ATTRIB |
                inotify.IN_CLOSE_WRITE |
                inotify.IN_CREATE |
                inotify.IN_DELETE |
                inotify.IN_MODIFY |
                inotify.IN_MOVED_FROM |
                inotify.IN_MOVED_TO
        )
        _ADD_MASK = (
                _TRIGGER_MASK |
                inotify.IN_EXCL_UNLINK |
                inotify.IN_ONLYDIR
        )

        def __init__(self, monitor):
            _BaseThread.__init__(self, monitor)
            worktree = git.worktree()
            if worktree is not None:
                worktree = core.abspath(worktree)
            self._worktree = worktree
            self._git_dir = git.git_path()
            self._lock = Lock()
            self._inotify_fd = None
            self._pipe_r = None
            self._pipe_w = None
            self._worktree_wd_to_path_map = {}
            self._worktree_path_to_wd_map = {}
            self._git_dir_wd_to_path_map = {}
            self._git_dir_path_to_wd_map = {}
            self._git_dir_wd = None

        @staticmethod
        def _log_out_of_wds_message():
            msg = N_('File system change monitoring: disabled because the'
                     ' limit on the total number of inotify watches was'
                     ' reached.  You may be able to increase the limit on'
                     ' the number of watches by running:\n'
                     '\n'
                     '    echo fs.inotify.max_user_watches=100000 |'
                     ' sudo tee -a /etc/sysctl.conf &&'
                     ' sudo sysctl -p\n')
            Interaction.safe_log(msg)

        def run(self):
            try:
                with self._lock:
                    self._inotify_fd = inotify.init()
                    self._pipe_r, self._pipe_w = os.pipe()

                poll_obj = select.poll()
                poll_obj.register(self._inotify_fd, select.POLLIN)
                poll_obj.register(self._pipe_r, select.POLLIN)

                self.refresh()

                self._log_enabled_message()

                while self._running:
                    if self._pending:
                        timeout = self._NOTIFICATION_DELAY
                    else:
                        timeout = None
                    try:
                        events = poll_obj.poll(timeout)
                    except OSError as e:
                        if e.errno == errno.EINTR:
                            continue
                        else:
                            raise
                    except select.error:
                        continue
                    else:
                        if not self._running:
                            break
                        elif not events:
                            self.notify()
                        else:
                            for fd, event in events:
                                if fd == self._inotify_fd:
                                    self._handle_events()
            finally:
                with self._lock:
                    if self._inotify_fd is not None:
                        os.close(self._inotify_fd)
                        self._inotify_fd = None
                    if self._pipe_r is not None:
                        os.close(self._pipe_r)
                        self._pipe_r = None
                        os.close(self._pipe_w)
                        self._pipe_w = None

        def refresh(self):
            with self._lock:
                if self._inotify_fd is None:
                    return
                try:
                    if self._worktree is not None:
                        tracked_dirs = set(
                                os.path.dirname(os.path.join(self._worktree,
                                                             path))
                                for path in gitcmds.tracked_files())
                        self._refresh_watches(tracked_dirs,
                                              self._worktree_wd_to_path_map,
                                              self._worktree_path_to_wd_map)
                    git_dirs = set()
                    git_dirs.add(self._git_dir)
                    for dirpath, dirnames, filenames in core.walk(
                            os.path.join(self._git_dir, 'refs')):
                        git_dirs.add(dirpath)
                    self._refresh_watches(git_dirs,
                                          self._git_dir_wd_to_path_map,
                                          self._git_dir_path_to_wd_map)
                    self._git_dir_wd = \
                            self._git_dir_path_to_wd_map[self._git_dir]
                except OSError as e:
                    if e.errno == errno.ENOSPC:
                        self._log_out_of_wds_message()
                        self._running = False
                    else:
                        raise

        def _refresh_watches(self, paths_to_watch, wd_to_path_map,
                             path_to_wd_map):
            watched_paths = set(path_to_wd_map)
            for path in watched_paths - paths_to_watch:
                wd = path_to_wd_map.pop(path)
                wd_to_path_map.pop(wd)
                try:
                    inotify.rm_watch(self._inotify_fd, wd)
                except OSError as e:
                    if e.errno == errno.EINVAL:
                        # This error can occur if the target of the wd was
                        # removed on the filesystem before we call
                        # inotify.rm_watch() so ignore it.
                        pass
                    else:
                        raise
            for path in paths_to_watch - watched_paths:
                try:
                    wd = inotify.add_watch(self._inotify_fd, core.encode(path),
                                           self._ADD_MASK)
                except OSError as e:
                    if e.errno in (errno.ENOENT, errno.ENOTDIR):
                        # These two errors should only occur as a result of
                        # race conditions:  the first if the directory
                        # referenced by path was removed or renamed before the
                        # call to inotify.add_watch(); the second if the
                        # directory referenced by path was replaced with a file
                        # before the call to inotify.add_watch().  Therefore we
                        # simply ignore them.
                        pass
                    else:
                        raise
                else:
                    wd_to_path_map[wd] = path
                    path_to_wd_map[path] = wd

        def _check_event(self, wd, mask, name):
            if mask & inotify.IN_Q_OVERFLOW:
                self._force_notify = True
            elif not mask & self._TRIGGER_MASK:
                pass
            elif mask & inotify.IN_ISDIR:
                pass
            elif wd in self._worktree_wd_to_path_map:
                if self._use_check_ignore and name:
                    path = os.path.join(self._worktree_wd_to_path_map[wd],
                                        core.decode(name))
                    self._file_paths.add(path)
                else:
                    self._force_notify = True
            elif wd == self._git_dir_wd:
                name = core.decode(name)
                if name == 'HEAD' or name == 'index':
                    self._force_notify = True
            elif (wd in self._git_dir_wd_to_path_map
                    and not core.decode(name).endswith('.lock')):
                self._force_notify = True

        def _handle_events(self):
            for wd, mask, cookie, name in \
                    inotify.read_events(self._inotify_fd):
                if not self._force_notify:
                    self._check_event(wd, mask, name)

        def stop(self):
            self._running = False
            with self._lock:
                if self._pipe_w is not None:
                    os.write(self._pipe_w, bchr(0))
            self.wait()


if AVAILABLE == 'pywin32':

    class _Win32Watch(object):

        def __init__(self, path, flags):
            self.flags = flags

            self.handle = None
            self.event = None

            try:
                self.handle = win32file.CreateFileW(
                        path,
                        0x0001,  # FILE_LIST_DIRECTORY
                        win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
                        None,
                        win32con.OPEN_EXISTING,
                        win32con.FILE_FLAG_BACKUP_SEMANTICS |
                        win32con.FILE_FLAG_OVERLAPPED,
                        None)

                self.buffer = win32file.AllocateReadBuffer(8192)
                self.event = win32event.CreateEvent(None, True, False, None)
                self.overlapped = pywintypes.OVERLAPPED()
                self.overlapped.hEvent = self.event
                self._start()
            except:
                self.close()
                raise

        def _start(self):
            win32file.ReadDirectoryChangesW(self.handle, self.buffer, True,
                                            self.flags, self.overlapped)

        def read(self):
            if win32event.WaitForSingleObject(self.event, 0) \
                    == win32event.WAIT_TIMEOUT:
                result = []
            else:
                nbytes = win32file.GetOverlappedResult(self.handle,
                                                       self.overlapped, False)
                result = win32file.FILE_NOTIFY_INFORMATION(self.buffer, nbytes)
                self._start()
            return result

        def close(self):
            if self.handle is not None:
                win32file.CancelIo(self.handle)
                win32file.CloseHandle(self.handle)
            if self.event is not None:
                win32file.CloseHandle(self.event)

    class _Win32Thread(_BaseThread):
        _FLAGS = (win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
                  win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
                  win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
                  win32con.FILE_NOTIFY_CHANGE_SIZE |
                  win32con.FILE_NOTIFY_CHANGE_LAST_WRITE |
                  win32con.FILE_NOTIFY_CHANGE_SECURITY)

        def __init__(self, monitor):
            _BaseThread.__init__(self, monitor)
            worktree = git.worktree()
            if worktree is not None:
                worktree = self._transform_path(core.abspath(worktree))
            self._worktree = worktree
            self._worktree_watch = None
            self._git_dir = self._transform_path(core.abspath(git.git_path()))
            self._git_dir_watch = None
            self._stop_event_lock = Lock()
            self._stop_event = None

        @staticmethod
        def _transform_path(path):
            return path.replace('\\', '/').lower()

        def _read_watch(self, watch):
            if win32event.WaitForSingleObject(watch.event, 0) \
                    == win32event.WAIT_TIMEOUT:
                nbytes = 0
            else:
                nbytes = win32file.GetOverlappedResult(watch.handle,
                                                       watch.overlapped, False)
            return win32file.FILE_NOTIFY_INFORMATION(watch.buffer, nbytes)

        def run(self):
            try:
                with self._stop_event_lock:
                    self._stop_event = win32event.CreateEvent(None, True,
                                                              False, None)

                events = [self._stop_event]

                if self._worktree is not None:
                    self._worktree_watch = _Win32Watch(self._worktree,
                                                       self._FLAGS)
                    events.append(self._worktree_watch.event)

                self._git_dir_watch = _Win32Watch(self._git_dir, self._FLAGS)
                events.append(self._git_dir_watch.event)

                self._log_enabled_message()

                while self._running:
                    if self._pending:
                        timeout = self._NOTIFICATION_DELAY
                    else:
                        timeout = win32event.INFINITE
                    rc = win32event.WaitForMultipleObjects(events, False,
                                                           timeout)
                    if not self._running:
                        break
                    elif rc == win32event.WAIT_TIMEOUT:
                        self.notify()
                    else:
                        self._handle_results()
            finally:
                with self._stop_event_lock:
                    if self._stop_event is not None:
                        win32file.CloseHandle(self._stop_event)
                        self._stop_event = None
                if self._worktree_watch is not None:
                    self._worktree_watch.close()
                if self._git_dir_watch is not None:
                    self._git_dir_watch.close()

        def _handle_results(self):
            if self._worktree_watch is not None:
                for action, path in self._worktree_watch.read():
                    if not self._running:
                        break
                    if self._force_notify:
                        continue
                    path = self._worktree + '/' + self._transform_path(path)
                    if (path != self._git_dir
                        and not path.startswith(self._git_dir + '/')
                        and not os.path.isdir(path)
                       ):
                        if self._use_check_ignore:
                            self._file_paths.add(path)
                        else:
                            self._force_notify = True
            for action, path in self._git_dir_watch.read():
                if not self._running:
                    break
                if self._force_notify:
                    continue
                path = self._transform_path(path)
                if path.endswith('.lock'):
                    continue
                if (path == 'head'
                    or path == 'index'
                    or path.startswith('refs/')
                   ):
                    self._force_notify = True

        def stop(self):
            self._running = False
            with self._stop_event_lock:
                if self._stop_event is not None:
                    win32event.SetEvent(self._stop_event)
            self.wait()


@memoize
def current():
    return _create_instance()


def _create_instance():
    thread_class = None
    cfg = gitcfg.current()
    if not cfg.get('cola.inotify', True):
        msg = N_('File system change monitoring: disabled because'
                 ' "cola.inotify" is false.\n')
        Interaction.log(msg)
    elif AVAILABLE == 'inotify':
        thread_class = _InotifyThread
    elif AVAILABLE == 'pywin32':
        thread_class = _Win32Thread
    else:
        if utils.is_win32():
            msg = N_('File system change monitoring: disabled because pywin32'
                     ' is not installed.\n')
            Interaction.log(msg)
        elif utils.is_linux():
            msg = N_('File system change monitoring: disabled because libc'
                     ' does not support the inotify system calls.\n')
            Interaction.log(msg)
    return _Monitor(thread_class)
