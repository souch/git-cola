"""Provides the main() routine and ColaApplication"""
from __future__ import division, absolute_import, unicode_literals
import argparse
import os
import signal
import sys

__copyright__ = """
Copyright (C) 2009-2016 David Aguilar and contributors
"""

from . import core
try:
    from qtpy import QtCore
except ImportError:
    errmsg = """
Sorry, you do not seem to have PyQt5, Pyside, or PyQt4 installed.
Please install it before using git-cola, e.g.:
    $ sudo apt-get install python-qt4
"""
    core.error(errmsg)

from qtpy import QtGui
from qtpy import QtWidgets

# Import cola modules
from .decorators import memoize
from .i18n import N_
from .interaction import Interaction
from .models import main
from .widgets import cfgactions
from .widgets import defs
from .widgets import startup
from .settings import Session
from . import cmds
from . import core
from . import compat
from . import fsmonitor
from . import git
from . import gitcfg
from . import icons
from . import i18n
from . import qtcompat
from . import qtutils
from . import resources
from . import version


def setup_environment():
    # Allow Ctrl-C to exit
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Session management wants an absolute path when restarting
    sys.argv[0] = sys_argv0 = os.path.abspath(sys.argv[0])

    # Spoof an X11 display for SSH
    os.environ.setdefault('DISPLAY', ':0')

    if not core.getenv('SHELL', ''):
        for shell in ('/bin/zsh', '/bin/bash', '/bin/sh'):
            if os.path.exists(shell):
                compat.setenv('SHELL', shell)
                break

    # Setup the path so that git finds us when we run 'git cola'
    path_entries = core.getenv('PATH', '').split(os.pathsep)
    bindir = core.decode(os.path.dirname(sys_argv0))
    path_entries.append(bindir)
    path = os.pathsep.join(path_entries)
    compat.setenv('PATH', path)

    # We don't ever want a pager
    compat.setenv('GIT_PAGER', '')

    # Setup *SSH_ASKPASS
    git_askpass = core.getenv('GIT_ASKPASS')
    ssh_askpass = core.getenv('SSH_ASKPASS')
    if git_askpass:
        askpass = git_askpass
    elif ssh_askpass:
        askpass = ssh_askpass
    elif sys.platform == 'darwin':
        askpass = resources.share('bin', 'ssh-askpass-darwin')
    else:
        askpass = resources.share('bin', 'ssh-askpass')

    compat.setenv('GIT_ASKPASS', askpass)
    compat.setenv('SSH_ASKPASS', askpass)

    # --- >8 --- >8 ---
    # Git v1.7.10 Release Notes
    # =========================
    #
    # Compatibility Notes
    # -------------------
    #
    #  * From this release on, the "git merge" command in an interactive
    #   session will start an editor when it automatically resolves the
    #   merge for the user to explain the resulting commit, just like the
    #   "git commit" command does when it wasn't given a commit message.
    #
    #   If you have a script that runs "git merge" and keeps its standard
    #   input and output attached to the user's terminal, and if you do not
    #   want the user to explain the resulting merge commits, you can
    #   export GIT_MERGE_AUTOEDIT environment variable set to "no", like
    #   this:
    #
    #        #!/bin/sh
    #        GIT_MERGE_AUTOEDIT=no
    #        export GIT_MERGE_AUTOEDIT
    #
    #   to disable this behavior (if you want your users to explain their
    #   merge commits, you do not have to do anything).  Alternatively, you
    #   can give the "--no-edit" option to individual invocations of the
    #   "git merge" command if you know everybody who uses your script has
    #   Git v1.7.8 or newer.
    # --- >8 --- >8 ---
    # Longer-term: Use `git merge --no-commit` so that we always
    # have a chance to explain our merges.
    compat.setenv('GIT_MERGE_AUTOEDIT', 'no')


def get_icon_themes():
    """Return the default icon theme names"""
    themes = []

    icon_themes_env = core.getenv('GIT_COLA_ICON_THEME')
    if icon_themes_env:
        themes.extend([x for x in icon_themes_env.split(':') if x])

    icon_themes_cfg = gitcfg.current().get_all('cola.icontheme')
    if icon_themes_cfg:
        themes.extend(icon_themes_cfg)

    if not themes:
        themes.append('light')

    return themes


# style note: we use camelCase here since we're masquerading a Qt class
class ColaApplication(object):
    """The main cola application

    ColaApplication handles i18n of user-visible data
    """

    def __init__(self, argv, locale=None, gui=True, icon_themes=None):
        cfgactions.install()
        i18n.install(locale)
        qtcompat.install()
        qtutils.install()
        icons.install(icon_themes or get_icon_themes())

        fsmonitor.current().files_changed.connect(self._update_files)

        if gui:
            self._app = current(tuple(argv))
            self._app.setWindowIcon(icons.cola())
            self._install_style()
        else:
            self._app = QtCore.QCoreApplication(argv)

    def _install_style(self):
        palette = self._app.palette()
        window = palette.color(QtGui.QPalette.Window)
        highlight = palette.color(QtGui.QPalette.Highlight)
        shadow = palette.color(QtGui.QPalette.Shadow)
        base = palette.color(QtGui.QPalette.Base)

        window_rgb = qtutils.rgb_css(window)
        highlight_rgb = qtutils.rgb_css(highlight)
        shadow_rgb = qtutils.rgb_css(shadow)
        base_rgb = qtutils.rgb_css(base)

        self._app.setStyleSheet("""
            QCheckBox::indicator {
                width: %(checkbox_size)spx;
                height: %(checkbox_size)spx;
            }
            QCheckBox::indicator::unchecked {
                border: %(checkbox_border)spx solid %(shadow_rgb)s;
                background: %(base_rgb)s;
            }
            QCheckBox::indicator::checked {
                image: url(%(checkbox_icon)s);
                border: %(checkbox_border)spx solid %(shadow_rgb)s;
                background: %(base_rgb)s;
            }

            QRadioButton::indicator {
                width: %(radio_size)spx;
                height: %(radio_size)spx;
            }
            QRadioButton::indicator::unchecked {
                border: %(radio_border)spx solid %(shadow_rgb)s;
                border-radius: %(radio_radius)spx;
                background: %(base_rgb)s;
            }
            QRadioButton::indicator::checked {
                image: url(%(radio_icon)s);
                border: %(radio_border)spx solid %(shadow_rgb)s;
                border-radius: %(radio_radius)spx;
                background: %(base_rgb)s;
            }

            QSplitter::handle:hover {
                background: %(highlight_rgb)s;
            }

            QMainWindow::separator {
                background: %(window_rgb)s;
                width: %(separator)spx;
                height: %(separator)spx;
            }
            QMainWindow::separator:hover {
                background: %(highlight_rgb)s;
            }

            """ % dict(separator=defs.separator,
                       window_rgb=window_rgb,
                       highlight_rgb=highlight_rgb,
                       shadow_rgb=shadow_rgb,
                       base_rgb=base_rgb,
                       checkbox_border=defs.border,
                       checkbox_icon=icons.check_name(),
                       checkbox_size=defs.checkbox,
                       radio_border=defs.radio_border,
                       radio_icon=icons.dot_name(),
                       radio_radius=defs.checkbox//2,
                       radio_size=defs.checkbox))

    def activeWindow(self):
        """Wrap activeWindow()"""
        return self._app.activeWindow()

    def desktop(self):
        return self._app.desktop()

    def exec_(self):
        """Wrap exec_()"""
        return self._app.exec_()

    def set_view(self, view):
        if hasattr(self._app, 'view'):
            self._app.view = view

    def _update_files(self):
        # Respond to file system updates
        cmds.do(cmds.Refresh)


@memoize
def current(argv):
    return ColaQApplication(list(argv))


class ColaQApplication(QtWidgets.QApplication):

    def __init__(self, argv):
        super(ColaQApplication, self).__init__(argv)
        self.view = None  # injected by application_start()

    def event(self, e):
        if e.type() == QtCore.QEvent.ApplicationActivate:
            cfg = gitcfg.current()
            if cfg.get('cola.refreshonfocus', False):
                cmds.do(cmds.Refresh)
        return super(ColaQApplication, self).event(e)

    def commitData(self, session_mgr):
        """Save session data"""
        if self.view is None:
            return
        sid = session_mgr.sessionId()
        skey = session_mgr.sessionKey()
        session_id = '%s_%s' % (sid, skey)
        session = Session(session_id, repo=core.getcwd())
        self.view.save_state(settings=session)


def process_args(args):
    if args.version:
        # Accept 'git cola --version' or 'git cola version'
        version.print_version()
        sys.exit(core.EXIT_SUCCESS)

    # Handle session management
    restore_session(args)

    # Bail out if --repo is not a directory
    repo = core.decode(args.repo)
    if repo.startswith('file:'):
        repo = repo[len('file:'):]
    repo = core.realpath(repo)
    if not core.isdir(repo):
        errmsg = N_('fatal: "%s" is not a directory.  '
                    'Please specify a correct --repo <path>.') % repo
        core.stderr(errmsg)
        sys.exit(core.EXIT_USAGE)


def restore_session(args):
    # args.settings is provided when restoring from a session.
    args.settings = None
    if args.session is None:
        return
    session = Session(args.session)
    if session.load():
        args.settings = session
        args.repo = session.repo


def application_init(args, update=False):
    """Parses the command-line arguments and starts git-cola
    """
    # Ensure that we're working in a valid git repository.
    # If not, try to find one.  When found, chdir there.
    setup_environment()
    process_args(args)

    app = new_application(args)
    model = new_model(app, args.repo,
                      prompt=args.prompt, settings=args.settings)
    if update:
        model.update_status()
    cfg = gitcfg.current()
    return ApplicationContext(args, app, cfg, model)


def application_start(context, view):
    """Show the GUI and start the main event loop"""
    # Store the view for session management
    context.app.set_view(view)

    # Make sure that we start out on top
    view.show()
    view.raise_()

    # Scan for the first time
    runtask = qtutils.RunTask(parent=view)
    init_update_task(view, runtask, context.model)

    # Start the filesystem monitor thread
    fsmonitor.current().start()

    QtCore.QTimer.singleShot(0, _send_msg)

    # Start the event loop
    result = context.app.exec_()

    # All done, cleanup
    fsmonitor.current().stop()
    QtCore.QThreadPool.globalInstance().waitForDone()

    return result


def add_common_arguments(parser):
    # We also accept 'git cola version'
    parser.add_argument('--version', default=False, action='store_true',
                        help='print version number')

    # Specifies a git repository to open
    parser.add_argument('-r', '--repo', metavar='<repo>', default=core.getcwd(),
                        help='open the specified git repository')

    # Specifies that we should prompt for a repository at startup
    parser.add_argument('--prompt', action='store_true', default=False,
                        help='prompt for a repository')

    # Specify the icon theme
    parser.add_argument('--icon-theme', metavar='<theme>',
                        dest='icon_themes', action='append', default=[],
                        help='specify an icon theme (name or directory)')

    # Resume an X Session Management session
    parser.add_argument('-session', metavar='<session>', default=None,
                        help=argparse.SUPPRESS)


def new_application(args):
    # Initialize the app
    return ColaApplication(sys.argv, icon_themes=args.icon_themes)


def new_model(app, repo, prompt=False, settings=None):
    model = main.model()
    valid = False
    if not prompt:
        valid = model.set_worktree(repo)
        if not valid:
            # We are not currently in a git repository so we need to find one.
            # Before prompting the user for a repository, check if they've
            # configured a default repository and attempt to use it.
            default_repo = gitcfg.current().get('cola.defaultrepo')
            if default_repo:
                valid = model.set_worktree(default_repo)

    while not valid:
        # If we've gotten into this loop then that means that neither the
        # current directory nor the default repository were available.
        # Prompt the user for a repository.
        startup_dlg = startup.StartupDialog(app.activeWindow(),
                                            settings=settings)
        gitdir = startup_dlg.find_git_repo()
        if not gitdir:
            sys.exit(core.EXIT_NOINPUT)
        valid = model.set_worktree(gitdir)

    return model


def init_update_task(parent, runtask, model):
    """Update the model in the background

    git-cola should startup as quickly as possible.

    """

    def update_status():
        model.update_status(update_index=True)

    task = qtutils.SimpleTask(parent, update_status)
    runtask.start(task)


def _send_msg():
    trace = git.GIT_COLA_TRACE
    if trace == '2' or trace == 'trace':
        msg1 = 'info: debug level 2: trace mode enabled'
        msg2 = 'info: set GIT_COLA_TRACE=1 for less-verbose output'
        Interaction.log(msg1)
        Interaction.log(msg2)
    elif trace:
        msg1 = 'info: debug level 1'
        msg2 = 'info: set GIT_COLA_TRACE=2 for trace mode'
        Interaction.log(msg1)
        Interaction.log(msg2)


class ApplicationContext(object):

    def __init__(self, args, app, cfg, model):
        self.args = args
        self.app = app
        self.cfg = cfg
        self.model = model
