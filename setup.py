#!/usr/bin/env python
"""git-cola installer

NOTE: This script is not typically invoked directly; use the Makefile
targets instead.

"""

from __future__ import absolute_import, division, unicode_literals

# Hacktastic hack to fix python's stupid ascii default encoding, which
# breaks inside distutils when installing from utf-8 paths.
import sys
try:
    # pylint: disable=reload-builtin
    reload(sys)
    # pylint: disable=no-member
    sys.setdefaultencoding('utf8')
except NameError:  # Python3
    pass

import os
from glob import glob
from distutils.core import setup

# Look for modules in the root
srcdir = os.path.dirname(os.path.abspath(__file__))

from extras import cmdclass

here = os.path.dirname(__file__)
version = os.path.join(here, 'cola', '_version.py')
scope = {}
exec(open(version).read(), scope)  # pylint: disable=exec-used
version = scope['VERSION']


def main():
    """Runs distutils.setup()"""
    vendor_libs = should_vendor_libs()

    scripts = [
        'bin/git-cola',
        'bin/git-dag',
    ]

    if sys.platform == 'win32':
        scripts.append('contrib/win32/cola')

    setup(name='git-cola',
          version=version,
          description='The highly caffeinated git GUI',
          long_description='A sleek and powerful git GUI',
          license='GPLv2',
          author='David Aguilar',
          author_email='davvid@gmail.com',
          url='https://git-cola.github.io/',
          scripts=scripts,
          cmdclass=cmdclass,
          platforms='any',
          data_files=_data_files(vendor_libs))


def should_vendor_libs():
    """Return True if we should include vendored libraries"""
    vendor_libs = not os.getenv('GIT_COLA_NO_VENDOR_LIBS', '')
    if '--no-vendor-libs' in sys.argv:
        sys.argv.remove('--no-vendor-libs')
        vendor_libs = False
    return vendor_libs


def _data_files(vendor_libs):
    """Return the list of data files"""
    data = [
        _app_path('share/git-cola/bin', '*'),
        _app_path('share/git-cola/icons', '*.png'),
        _app_path('share/git-cola/icons', '*.svg'),
        _app_path('share/git-cola/icons/dark', '*.png'),
        _app_path('share/git-cola/icons/dark', '*.svg'),
        _app_path('share/appdata', '*.xml'),
        _app_path('share/applications', '*.desktop'),
        _app_path('share/doc/git-cola', '*.rst'),
        _app_path('share/doc/git-cola', '*.html'),
        _package('cola'),
        _package('cola.models'),
        _package('cola.widgets'),
    ]

    if vendor_libs:
        data.extend([
            _package('qtpy'),
            _package('qtpy._patch'),
        ])

    data.extend([_app_path(localedir, 'git-cola.mo')
                 for localedir in glob('share/locale/*/LC_MESSAGES')])
    return data


def _package(package, subdirs=None):
    """Collect python files for a given python "package" name"""
    dirs = package.split('.')
    app_dir = os.path.join('share', 'git-cola', 'lib', *dirs)
    if subdirs:
        dirs = list(subdirs) + dirs
    src_dir = os.path.join(*dirs)
    return (app_dir, glob(os.path.join(src_dir, '*.py')))


def _app_path(dirname, entry):
    """Construct (dirname, [glob-expanded-entries relative to dirname])"""
    return (dirname, glob(os.path.join(dirname, entry)))


if __name__ == '__main__':
    main()
