# Copyright (c) David Aguilar
"""Provide git-cola's version number"""
from __future__ import division, absolute_import, unicode_literals

import os
import sys

if __name__ == '__main__':
    srcdir = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(1, srcdir)

from .git import git
from .git import STDOUT
from .decorators import memoize
from ._version import VERSION

# minimum version requirements
_versions = {
    # git diff learned --patience in 1.6.2
    # git mergetool learned --no-prompt in 1.6.2
    # git difftool moved out of contrib in git 1.6.3
    'git': '1.6.3',
    'python': '2.6',
    # git diff --submodule was introduced in 1.6.6
    'diff-submodule': '1.6.6',
    # git check-ignore was introduced in 1.8.2, but did not follow the same
    # rules as git add and git status until 1.8.5
    'check-ignore': '1.8.5',
    # git for-each-ref --sort=version:refname
    'version-sort': '2.7.0',
}


def get(key):
    """Returns an entry from the known versions table"""
    return _versions.get(key)


def version():
    """Returns the current version"""
    return VERSION


@memoize
def check_version(min_ver, ver):
    """Check whether ver is greater or equal to min_ver
    """
    min_ver_list = version_to_list(min_ver)
    ver_list = version_to_list(ver)
    return min_ver_list <= ver_list


@memoize
def check(key, ver):
    """Checks if a version is greater than the known version for <what>"""
    return check_version(get(key), ver)


def check_git(key):
    """Checks if Git has a specific feature"""
    return check(key, git_version())


def version_to_list(version):
    """Convert a version string to a list of numbers or strings
    """
    ver_list = []
    for p in version.split('.'):
        try:
            n = int(p)
        except ValueError:
            n = p
        ver_list.append(n)
    return ver_list


@memoize
def git_version_str():
    """Returns the current GIT version"""
    return git.version()[STDOUT].strip()


@memoize
def git_version():
    """Returns the current GIT version"""
    parts = git_version_str().split()
    if parts and len(parts) >= 3:
        return parts[2]
    else:
        # minimum supported version
        return '1.6.3'


def cola_version():
    return 'cola version %s' % version()


def print_version(brief=False):
    if brief:
        msg = version()
    else:
        msg = cola_version()
    sys.stdout.write('%s\n' % msg)


if __name__ == '__main__':
    print_version(brief=True)
