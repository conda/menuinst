# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2013-2017 Continuum Analytics, Inc.
# Copyright (c) 2008-2011 by Enthought, Inc.
# All rights reserved.
#
# Licensed under the terms of the BSD 3-clause License (See LICENSE.txt)
# -----------------------------------------------------------------------------
"""Menuinst api."""

from __future__ import absolute_import

# Standard library imports
import json
import logging
import os
import sys


if sys.platform.startswith('linux'):
    from .linux import Menu, ShortCut

elif sys.platform == 'darwin':
    from .darwin import Menu, ShortCut

elif sys.platform == 'win32':
    from .win32 import Menu, ShortCut
    from .win_elevate import isUserAdmin, runAsAdmin


def _install(path, remove=False, prefix=sys.prefix, mode=None):
    """Install Menu and shortcuts helper."""
    if os.path.abspath(prefix) == os.path.abspath(sys.prefix):
        env_name = None
    else:
        env_name = os.path.basename(prefix)

    data = json.load(open(path))
    try:
        menu_name = data['menu_name']
    except KeyError:
        menu_name = 'Python-%d.%d' % sys.version_info[:2]

    shortcuts = data['menu_items']
    m = Menu(menu_name, prefix=prefix, env_name=env_name, mode=mode)
    if remove:
        for sc in shortcuts:
            ShortCut(m, sc).remove()
        m.remove()
    else:
        m.create()
        for sc in shortcuts:
            ShortCut(m, sc).create()


def install(path, remove=False, prefix=sys.prefix):
    """Install Menu and shortcuts."""
    noadmin_path = os.path.join(sys.prefix, '.nonadmin')
    if (sys.platform == 'win32' and not os.path.exists(noadmin_path) and
            not isUserAdmin()):
        from pywintypes import error
        try:
            runAsAdmin(['pythonw', '-c',
                        "import menuinst; menuinst.api.install(%r, %r, %r)" % (
                            path, bool(remove), prefix)])
        except error:
            logging.warn("Insufficient permissions to write menu folder.  "
                         "Falling back to user location")
            _install(path, remove, prefix, mode='user')
    else:
        _install(path, remove, prefix)
