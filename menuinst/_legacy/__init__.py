# Copyright (c) 2008-2011 by Enthought, Inc.
# Copyright (c) 2013-2015 Continuum Analytics, Inc.
# All rights reserved.

from __future__ import absolute_import
import logging
import sys
import json
from os.path import abspath, basename, exists, join

try:
    from .._version import __version__
except ImportError:
    __version__ = "dev"

from ..utils import DEFAULT_PREFIX, DEFAULT_BASE_PREFIX

if sys.platform == 'win32':
    from .win32 import Menu, ShortCut
    from ..platforms.win_utils.win_elevate import isUserAdmin, runAsAdmin


def _install(path, remove=False, prefix=DEFAULT_PREFIX, mode=None, root_prefix=DEFAULT_BASE_PREFIX):
    if abspath(prefix) == abspath(root_prefix):
        env_name = None
    else:
        env_name = basename(prefix)

    data = json.load(open(path))
    try:
        menu_name = data['menu_name']
    except KeyError:
        menu_name = 'Python-%d.%d' % sys.version_info[:2]

    shortcuts = data['menu_items']
    m = Menu(menu_name, prefix=prefix, env_name=env_name, mode=mode, root_prefix=root_prefix)
    if remove:
        for sc in shortcuts:
            ShortCut(m, sc).remove()
        m.remove()
    else:
        m.create()
        for sc in shortcuts:
            ShortCut(m, sc).create()


def install(path, remove=False, prefix=DEFAULT_PREFIX, recursing=False, root_prefix=DEFAULT_BASE_PREFIX):
    """
    Install Menu and shortcuts

    # Specifying `root_prefix` is used with conda-standalone, because we can't use
    # `sys.prefix`, therefore we need to specify it
    """
    if not sys.platform == 'win32':
        raise RuntimeError("menuinst._legacy is only supported on Windows.")

    # this root_prefix is intentional.  We want to reflect the state of the root installation.

    if not exists(join(root_prefix, '.nonadmin')):
        if isUserAdmin():
            _install(path, remove, prefix, mode='system', root_prefix=root_prefix)
        else:
            retcode = 1
            try:
                if not recursing:
                    retcode = runAsAdmin([join(root_prefix, 'python'), '-c',
                                          "import menuinst; menuinst.install(%r, %r, %r, %r, %r)" % (
                                              path, bool(remove), prefix, True, root_prefix)])
            except OSError:
                pass

            if retcode != 0:
                logging.warn("Insufficient permissions to write menu folder.  "
                             "Falling back to user location")
                _install(path, remove, prefix, mode='user', root_prefix=root_prefix)
    else:
        _install(path, remove, prefix, mode='user', root_prefix=root_prefix)
