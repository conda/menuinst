"""
"""
import os
import warnings
from pathlib import Path
from typing import Tuple, Union

from win32com.client import Dispatch

from .base import Menu, MenuItem
from ..utils import WinLex

# TODO: Reimplement/port to get rid of _legacy
from .._legacy.win32 import folder_path


class WindowsMenu(Menu):
    def create(self):
        # TODO: Check if elevated permissions are needed
        self.start_menu_location.mkdir(parents=True, exist_ok=False)
        return (self.start_menu_location,)

    def remove(self):
        # TODO: Check if elevated permissions are needed
        self.start_menu_location.rmdir()
        return (self.start_menu_location,)

    @property
    def start_menu_location(self):
        """
        On Windows we can create shortcuts in several places:

        - Start Menu
        - Desktop
        - Quick launch (only for user installs)

        In this property we only report the path to the Start menu.
        For other menus, check their respective properties.
        """
        return Path(folder_path(self.mode, False, "start")) / self.name

    @property
    def quick_launch_location(self):
        if self.mode == "system":
            warnings.warn("Quick launch menus are not available for system level installs")
            return
        return Path(folder_path(self.mode, False, "quicklaunch"))

    @property
    def desktop_location(self):
        return Path(folder_path(self.mode, False, "desktop"))

    @property
    def placeholders(self):
        placeholders = super().placeholders
        placeholders.update(
            {
                "SCRIPTS_DIR": os.path.join(self.prefix, "Scripts"),
                "CWP": os.path.join(self.prefix, "cwp.py"),
                "PYTHON": os.path.join(self.prefix, "python.exe"),
                "PYTHONW": os.path.join(self.prefix, "pythonw.exe"),
                "BASE_PYTHON": os.path.join(self.base_prefix, "python.exe"),
                "BASE_PYTHONW": os.path.join(self.base_prefix, "pythonw.exe"),
                "BIN_DIR": os.path.join(self.prefix, "Library", "bin"),
                "SP_DIR": os.path.join(self.prefix, "Lib", "site-packages"),
                "ICON_EXT": "ico",
            }
        )
        return placeholders

    def render(self, value: Union[str, None], slug: bool = False):
        """
        We extend the render method here to replace forward slashes with backslashes.
        We ONLY do it if the string does not start with /, because it might
        be just a windows-style command-line flag (e.g. cmd /K something).

        This will not escape strings such as `/flag:something`, common
        in compiler stuff but we can assume such windows specific
        constructs will have their platform override, which is always an option.

        This is just a convenience for things like icon paths or Unix-like paths
        in the command key.
        """
        value = super().render(value, slug=slug)
        if value is None:
            return value
        if "/" in value and value[0] != "/":
            value = value.replace("/", "\\")
        return value


class WindowsMenuItem(MenuItem):
    def create(self) -> Tuple[Path]:
        shell = Dispatch("WScript.Shell")
        activate = self.metadata.activate

        if activate:
            script = self._write_script()
        paths = self._paths()

        for path in paths:
            if not path.suffix == ".lnk":
                continue

            shortcut = shell.CreateShortCut(str(path))

            if activate:
                if self.metadata.no_console:
                    command = [
                        "powershell.exe",
                        f'"start \"{script}\" -WindowStyle hidden"',
                    ]
                else:
                    command = [
                        "cmd.exe",
                        "/K",
                        script,
                    ]
            else:
                command = self.render("command")

            target_path, *arguments = WinLex.quote_args(command)

            shortcut.Targetpath = target_path
            if arguments:
                shortcut.Arguments = " ".join(arguments)

            working_dir = self.render("working_dir")
            if working_dir:
                Path(working_dir).mkdir(parents=True, exist_ok=True)
            else:
                working_dir = "%HOMEPATH%"
            shortcut.WorkingDirectory = working_dir

            icon = self.render("icon")
            if icon:
                shortcut.IconLocation = icon

            # TODO: Check if elevated permissions are needed
            shortcut.save()
        return paths

    def remove(self) -> Tuple[Path]:
        paths = self._paths()
        for path in paths:
            # TODO: Check if elevated permissions are needed
            os.unlink(path)
        return paths

    def _paths(self):
        directories = [self.menu.start_menu_location]
        if self.metadata.desktop:
            directories.append(self.menu.desktop_location)
        if self.metadata.quicklaunch and self.menu.quick_launch_location:
            directories.append(self.menu.quick_launch_location)

        # These are the different lnk files
        shortcuts = [directory / self._shortcut_filename() for directory in directories]

        if self.metadata.activate:
            # This is the accessory launcher script for cmd
            shortcuts.append(self._path_for_script())

        return tuple(shortcuts)

    def _shortcut_filename(self, ext="lnk"):
        env_suffix = f" ({self.menu.env_name})" if self.menu.env_name else ""
        return f"{self.render('name')}{env_suffix}.{ext}"

    def _path_for_script(self):
        return Path(self.menu.placeholders["{{ MENU_DIR }}"]) / self._shortcut_filename("bat")

    def _write_script(self):
        """
        This method generates the batch script that will be called by the shortcut
        """
        lines = ["@echo off"]
        if self.metadata.activate:
            lines += [
                "SETLOCAL ENABLEDELAYEDEXPANSION",
                f'set "BASE_PREFIX={self.menu.placeholders["{{ BASE_PREFIX }}"]}"',
                f'set "PREFIX={self.menu.placeholders["{{ PREFIX }}"]}"',
                'FOR /F "usebackq tokens=*" %%i IN (`%BASE_PREFIX%\_conda.exe shell.cmd.exe activate "%PREFIX%"`) do set "ACTIVATOR=%%i"',
                'CALL %ACTIVATOR%',
                ":: This below is the user command"
            ]

        lines += self.render("command")

        path = self._path_for_script()
        with open(path, "w") as f:
            f.write("\r\n".join(lines))

        return path