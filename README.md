# git-cola: The highly caffeinated Git GUI

    git-cola is a powerful Git GUI with a slick and intuitive user interface.

    Copyright (C) 2007-2017, David Aguilar and contributors

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

## SCREENSHOTS

Screenshots are available on the
[git-cola screenshots page](https://git-cola.github.io/screenshots.html).

## DOWNLOAD

    apt-get install git-cola

New releases are available on the
[git-cola download page](https://git-cola.github.io/downloads.html).

## FORK

    git clone git://github.com/git-cola/git-cola.git

[![git-cola build status](https://api.travis-ci.org/git-cola/git-cola.svg?branch=master)](https://travis-ci.org/git-cola/git-cola)

[git-cola on github](https://github.com/git-cola/git-cola)

[git-cola google group](http://groups.google.com/group/git-cola/)


# NUTRITIONAL FACTS

## ACTIVE INGREDIENTS

* [git](http://git-scm.com/) 1.6.3 or newer.

* [Python](http://python.org/) 2.6, 2.7, and 3.2 or newer.

* [QtPy](https://github.com/spyder-ide/qtpy) 1.1.0 or newer.

* [argparse](https://pypi.python.org/pypi/argparse) 1.1 or newer.
  argparse is part of the stdlib in Python 2.7; install argparse separately if
  you are running on Python 2.6.

* [Sphinx](http://sphinx-doc.org/) for building the documentation.

*git-cola* uses *QtPy*, so you can choose between *PyQt4*, *PyQt5*, and
*PySide* by setting the `QT_API` environment variable to `pyqt4`, `pyqt5` or
`pyside` as desired.  `qtpy` defaults to `pyqt5` and falls back to `pyqt4`
if `pyqt5` is not installed.

Any of the following Python Qt libraries must be installed:

* [PyQt4](https://www.riverbankcomputing.com/software/pyqt/download)
  4.6 or newer

* [PyQt5](https://www.riverbankcomputing.com/software/pyqt/download5)
  5.2 or newer

* [PySide](https://github.com/PySide/PySide)
  1.1.0 or newer

*NOTE*: We do not yet recommend using *PyQt5* because there are known
exit-on-segfault bugs in *Qt5* that have not yet been addressed.
*git-cola* is sensitive to this bug and is known to crash on exit
when using `git dag` or the interactive rebase feature on *PyQt5*.

[QTBUG-52988](https://bugreports.qt.io/browse/QTBUG-52988)

*PyQt4* is stable and there are no known issues when using it so we recommend
using *PyQt4* until the *Qt5* bugs have been resolved.

Set `QT_API=pyqt4` in your environment if you have both
versions of *PyQt* installed and want to ensure that PyQt4 is used.

*NOTE*: *git-cola* includes a vendored copy of its *QtPy* dependency.

We provide a copy of the `qtpy` module when installing *git-cola* so that you
are not required to install *QtPy* separately.  If you'd like to provide your
own `qtpy` module, for example from the `python-qtpy` Debian package, then use
`make NO_VENDOR_LIBS=1 ...` when invoking `make`, or export
`GIT_COLA_NO_VENDOR_LIBS=1` into the build environment.


## ADDITIVES

*git-cola* enables additional features when the following
Python modules are installed.

[send2trash](https://github.com/hsoft/send2trash) enables cross-platform
"Send to Trash" functionality.

# BREWING INSTRUCTIONS

## RUN FROM SOURCE

You don't need to install *git-cola* to run it.
Running *git-cola* from its source tree is the easiest
way to try the latest version.

    git clone git://github.com/git-cola/git-cola.git
    cd git-cola
    ./bin/git-cola
    ./bin/git-dag

Having *git-cola*'s *bin/* directory in your path allows you to run
*git cola* like a regular built-in Git command:

    # Replace "$PWD/bin" with the path to git-cola's bin/ directory
    PATH="$PWD/bin":"$PATH"
    export PATH

    git cola
    git dag

The instructions below assume that you have *git-cola* present in your
`$PATH`.  Replace "git cola" with "./bin/git-cola" as needed if you'd like to
just run it in-place.

# DOCUMENTATION

* [HTML documentation](https://git-cola.readthedocs.io/en/latest/)

* [git-cola manual](share/doc/git-cola/git-cola.rst)

* [git-dag manual](share/doc/git-cola/git-dag.rst)

* [Keyboard shortcuts](https://git-cola.github.io/share/doc/git-cola/hotkeys.html)

* [Contributing guidelines](CONTRIBUTING.md)

# INSTALLATION

Normally you can just do "make install" to install *git-cola*
in your `$HOME` directory (`$HOME/bin`, `$HOME/share`, etc).
If you want to do a global install you can do

    make prefix=/usr install

The platform-specific installation methods below use the native
package manager.  You should use one of these so that all of *git-cola*'s
dependencies are installed.

## LINUX

Linux is it! Your distro has probably already packaged git-cola.
If not, please file a bug against your distribution ;-)

### arch

    yaourt -S git-cola

### debian, ubuntu

    apt-get install git-cola

### fedora

    dnf install git-cola

### gentoo

    emerge git-cola

### opensuse

Use the [one-click install link](http://software.opensuse.org/package/git-cola).


## MAC OS X

[Homebrew](http://brew.sh/) is the easiest way to install
git-cola's *Qt4* and *PyQt4* dependencies.  We will use Homebrew to install
the git-cola recipe, but build our own .app bundle from source.

[Sphinx](http://sphinx-doc.org/latest/install.html) is used to build the
documentation.

    brew install sphinx-doc
    brew install git-cola

Once brew has installed git-cola you can:

1. Clone git-cola

    `git clone git://github.com/git-cola/git-cola.git && cd git-cola`

2. Build the git-cola.app application bundle

    ```
    make \
        PYTHON=$(brew --prefix python3)/bin/python3 \
        PYTHON_CONFIG=$(brew --prefix python3)/bin/python3-config \
        SPHINXBUILD=$(brew --prefix sphinx-doc)/bin/sphinx-build \
        git-cola.app
   ```

3. Copy it to _/Applications_

    `rm -fr /Applications/git-cola.app && cp -r git-cola.app /Applications`

Newer versions of Homebrew install their own `python3` installation and
provide the `PyQt5` modules for `python3` only.  You have to use
`python3 ./bin/git-cola` when running from the source tree.

### UPGRADING USING HOMEBREW

If you upgrade using `brew` then it is recommended that you re-install
*git-cola*'s dependencies when upgrading.  Re-installing ensures that the
Python modules provided by Homebrew will be properly setup.

This is required when upgrading to a modern (post-10.11 El Capitan) Mac OS X.
Homebrew now bundles its own Python3 installation instead of using the
system-provided default Python.


    # update homebrew
    brew update

    # uninstall git-cola and its dependencies
    brew uninstall git-cola
    brew uninstall pyqt5
    brew uninstall sip

    # re-install git-cola and its dependencies
    brew install git-cola

## WINDOWS INSTALLATION

**IMPORTANT** If you have a 64-bit machine, install the 64-bit versions only.
Do not mix 32-bit and 64-bit versions.

Download and install the following:

* [Git for Windows](https://git-for-windows.github.io/)

* [Python](https://www.python.org/downloads/)
  * Python 3.4 is recommended.  Python 2.7 is also supported.
  * [64-bit](https://www.python.org/ftp/python/3.4.4/python-3.4.4.amd64.msi)
  * [32-bit](https://www.python.org/ftp/python/3.4.4/python-3.4.4.msi)

* [PyQt](https://riverbankcomputing.com/software/pyqt/download/)
  * PyQt4 4.11 is recommended.  PyQt4 requires a matching Python version.
  * [64-bit](http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.11.4/PyQt4-4.11.4-gpl-Py3.4-Qt4.8.7-x64.exe)
  * [32-bit](http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.11.4/PyQt4-4.11.4-gpl-Py3.4-Qt4.8.7-x32.exe)

* [Git Cola](https://github.com/git-cola/git-cola/downloads)

Once these are installed you can run *git cola* from the Start menu or
by double-clicking on the `git-cola.pyw` script.

If you are developing *git cola* on Windows you can use `python.exe` to run
directly from the source tree.  For example, from a Git Bash terminal:

    /c/Python34/python.exe ./bin/git-cola

See "WINDOWS (continued)" below for more details.

# GOODIES

*git-cola* ships with an interactive rebase editor called *git-xbase*.
*git-xbase* can be used to reorder and choose commits and is typically
launched through the *git-cola*'s "Rebase" menu.

*git-xbase* can also be launched independently of the main *git-cola* interface
by telling `git rebase` to use it as its editor:

    env GIT_SEQUENCE_EDITOR="$PWD/share/git-cola/bin/git-xbase" \
    git rebase -i origin/master

The quickest way to launch *git-xbase* is via the *git cola rebase*
sub-command (as well as various other sub-commands):

    git cola rebase origin/master

# COMMAND-LINE TOOLS

The *git-cola* command exposes various sub-commands that allow you to quickly
launch tools that are available from within the *git-cola* interface.
For example, `./bin/git-cola find` launches the file finder,
and `./bin/git-cola grep` launches the grep tool.

See `git cola --help-commands` for the full list of commands.

    $ git cola --help-commands
    usage: git-cola [-h]
    
                    {cola,am,archive,branch,browse,classic,config,
                     dag,diff,fetch,find,grep,merge,pull,push,
                     rebase,remote,search,stash,tag,version}
                    ...
    
    valid commands:
      {cola,am,archive,branch,browse,classic,config,
       dag,diff,fetch,find,grep,merge,pull,push,
       rebase,remote,search,stash,tag,version}

        cola                start git-cola
        am                  apply patches using "git am"
        archive             save an archive
        branch              create a branch
        browse              browse repository
        classic             browse repository
        config              edit configuration
        dag                 start git-dag
        diff                view diffs
        fetch               fetch remotes
        find                find files
        grep                grep source
        merge               merge branches
        pull                pull remote branches
        push                push remote branches
        rebase              interactive rebase
        remote              edit remotes
        search              search commits
        stash               stash and unstash changes
        tag                 create tags
        version             print the version

## HACKING

The following commands should be run during development:

    # Run the unit tests
    $ make test

    # Check for pylint warnings.  All new code must pass 100%.
    $ make pylint3k

The test suite can be found in the [test](test) directory.

The tests are setup to run automatically when code is pushed using
[Travis CI](https://travis-ci.org/git-cola/git-cola).
Checkout the [Travis config file](.travis.yml) for more details.

When submitting patches, consult the [contributing guidelines](CONTRIBUTING.md).

# WINDOWS (continued)

## BUILDING WINDOWS INSTALLERS

Windows installers are built using

* [Pynsist](http://pynsist.readthedocs.io/en/latest/).

* [NSIS](http://nsis.sourceforge.net/Main_Page) is also needed.

To build the installer using *Pynsist*:

* If building from a non-Windows platform run
  `./contrib/win32/fetch_pyqt_windows.sh`.
  This will download a PyQt binary installer for Windows and unpack its files
  into `pynsist_pkgs/`.

* Run `pynsist pynsist.cfg`.
  The installer will be built in `build/nsis/`.

Before *Pynsist*, installers were built using *InnoSetup*.
The *InnoSetup* scripts are still available:

    ./contrib/win32/create-installer.sh

You have to make sure that the file */share/InnoSetup/ISCC.exe* exists.

## WINDOWS HISTORY BROWSER CONFIGURATION UPGRADE

You may need to configure your history browser if you are upgrading from an
older version of *git-cola*.

`gitk` was originally the default history browser, but `gitk` cannot be
launched as-is on Windows because `gitk` is a shell script.

If you are configured to use `gitk`, then change your configuration to
go through Git's `sh.exe` on Windows.  Similarly,we must go through
`python.exe` if we want to use `git-dag`.

If you want to use *gitk* as your history browser open the
*Preferences* screen and change the history browser command to:

    "C:/Program Files/Git/bin/sh.exe" --login -i C:/Git/bin/gitk

Alternatively, if you'd like to use *git-dag* as your history browser, use:

    C:/Python34/python.exe C:/git-cola/bin/git-dag

*git-dag* became the default history browser on Windows in `v2.3`, so new
users should not need to configure anything.
