# Copyright (c) 2008-2011 by Enthought, Inc.
# Copyright (c) 2013-2015 Continuum Analytics, Inc.
# All rights reserved.

from __future__ import absolute_import
import sys
import json
import subprocess
import tempfile
from os.path import abspath, basename, exists, join

from ._version import get_versions

__version__ = get_versions()['version']

if sys.platform.startswith('linux'):
    from .linux import Menu, ShortCut

elif sys.platform == 'darwin':
    from .darwin import Menu, ShortCut

elif sys.platform == 'win32':
    from .win32 import Menu, ShortCut, dirs
    from .win_elevate import isUserAdmin, runAsAdmin


def _install(path, remove=False, prefix=sys.prefix):
    if abspath(prefix) == abspath(sys.prefix):
        env_name = None
    else:
        env_name = basename(prefix)

    data = json.load(open(path))
    try:
        menu_name = data['menu_name']
    except KeyError:
        menu_name = 'Python-%d.%d' % sys.version_info[:2]

    shortcuts = data['menu_items']
    m = Menu(menu_name)
    if remove:
        for sc in shortcuts:
            ShortCut(m, sc, target_prefix=prefix,
                     env_name=env_name).remove()
        m.remove()
    else:
        m.create()
        for sc in shortcuts:
            ShortCut(m, sc, target_prefix=prefix,
                     env_name=env_name).create()


def install(path, remove=False, prefix=sys.prefix):
    """
    install Menu and shortcuts
    """
    if sys.platform == 'win32' and not exists(join(sys.prefix, '.nonadmin')) and not isUserAdmin():
        runAsAdmin(['pythonw', '-c',
                    "import menuinst; menuinst.install(%r, %r, %r)" % (path, bool(remove), prefix)])
    else:
        _install(path, remove, prefix)


from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
