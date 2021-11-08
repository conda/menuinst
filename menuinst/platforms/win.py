"""
"""
import os
import shutil
import warnings

from win32com.client import Dispatch

from .base import Menu, MenuItem

# TODO: Reimplement/port to get rid of _legacy
from .._legacy.win32 import folder_path


class WindowsMenu(Menu):
    def create(self):
        # TODO: Check if elevated permissions are needed
        os.makedirs(self.start_menu_location)

    def remove(self):
        # TODO: Check if elevated permissions are needed
        shutil.rmtree(self.start_menu_location)

    @property
    def location(self):
        """
        On Windows we can create shortcuts in several places:

        - Start Menu
        - Desktop
        - Quick launch (only for user installs)

        In this property we only report the path to the Start menu.
        For other menus, check their respective properties.
        """
        return folder_path(self.mode, False, "start", self.render(self.name))

    start_menu_location = location

    @property
    def quick_launch_location(self):
        if self.mode == "system":
            warnings.warn("Quick launch menus are not available for system level installs")
            return
        return folder_path(self.mode, False, "quicklaunch")

    @property
    def desktop_location(self):
        return folder_path(self.mode, False, "desktop")

    @property
    def placeholders(self):
        placeholders = super().placeholders
        placeholders.update(
            {
                "{{ SCRIPTS_DIR }}": os.path.join(self.prefix, "Scripts"),
                "{{ CWP }}": os.path.join(self.prefix, "cwp.py"),
                "{{ PYTHON }}": os.path.join(self.prefix, "python.exe"),
                "{{ PYTHONW }}": os.path.join(self.prefix, "pythonw.exe"),
                "{{ BASE_PYTHON }}": os.path.join(self.base_prefix, "python.exe"),
                "{{ BASE_PYTHONW }}": os.path.join(self.base_prefix, "pythonw.exe"),
                "{{ BIN_DIR }}": os.path.join(self.prefix, "Library", "bin"),
                "{{ SP_DIR }}": os.path.join(self.prefix, "Lib", "site-packages"),
                "{{ ICON_EXT }}": "ico",
            }
        )
        return placeholders


class WindowsMenuItem(MenuItem):
    def create(self):
        shell = Dispatch("WScript.Shell")

        for path in self._paths():
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = self.render("command")
            shortcut.WorkingDirectory = self.render("working_dir")
            icon = self.value_for("icon")
            if icon:
                shortcut.IconLocation = self.menu.render(icon)
            # TODO: Check if elevated permissions are needed
            shortcut.save()

    def remove(self):
        for path in self._paths():
            # TODO: Check if elevated permissions are needed
            os.unlink(path)

    def _paths(self):
        directories = [self.menu.smart_menu_location]
        if self.metadata.platforms.win.quicklaunch:
            directories.append(self.menu.quick_launch_location)
        if self.metadata.platforms.win.desktop:
            directories.append(self.menu.desktop_location)

        filename = f"{self.render('name')}.lnk"
        return [os.path.join(directory, filename) for directory in directories]
