# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2013-2017 Continuum Analytics, Inc.
# Copyright (c) 2008-2011 by Enthought, Inc.
# All rights reserved.
#
# Licensed under the terms of the BSD 3-clause License (See LICENSE.txt)
# -----------------------------------------------------------------------------
"""Menuinst tests."""

# Standard library imports
import os
import sys

# Third party imports
import pytest

# Local imports
import menuinst


menu_dir = os.path.dirname(__file__)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only tests")
class TestWindowsShortcuts(object):

    def test_install_folders_exist(self):
        from menuinst import dirs_src
        for mode in ["user", "system"]:
            for path, _ in dirs_src[mode].values():
                assert os.path.exists(path)

    def test_create_and_remove_shortcut(self):
        nonadmin=os.path.join(sys.prefix, ".nonadmin")
        shortcut = os.path.join(menu_dir, "menu-windows.json")
        has_nonadmin = os.path.exists(nonadmin)
        for mode in ["user", "system"]:
            if mode=="user":
                open(nonadmin, 'a').close()
            menuinst.api.install(shortcut, remove=False)
            menuinst.api.install(shortcut, remove=True)
            if os.path.exists(nonadmin):
                os.remove(nonadmin)
        if has_nonadmin:
            open(nonadmin, 'a').close()
