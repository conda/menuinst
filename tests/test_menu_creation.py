import os
import sys

import pytest

import menuinst


menu_dir = os.path.dirname(__file__)

@pytest.mark.skipif(sys.platform != "win32",
                    reason="Windows-only tests")
class TestWindowsShortcuts(object):

    def test_install_folders_exist(self):
        from menuinst import dirs
        for mode in ["user", "system"]:
            for path in dirs[mode].values():
                assert os.path.exists(path)

    def test_create_and_remove_shortcut(self):
        nonadmin=os.path.join(sys.prefix, ".nonadmin")
        shortcut = os.path.join(menu_dir, "menu-windows.json")
        has_nonadmin = os.path.exists(nonadmin)
        for mode in ["user", "system"]:
            if mode=="user":
                open(nonadmin, 'a').close()
            menuinst.install(shortcut, remove=False)
            menuinst.install(shortcut, remove=True)
            if os.path.exists(nonadmin):
                os.remove(nonadmin)
        if has_nonadmin:
            open(nonadmin, 'a').close()
