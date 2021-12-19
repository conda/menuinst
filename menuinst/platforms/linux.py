"""
"""
import os
from pathlib import Path
import shutil
import xml.etree.ElementTree as XMLTree
import time
from logging import getLogger
from typing import Union, Iterable

from .base import Menu, MenuItem
from ..schema import MenuInstSchema
from ..utils import indent_xml_tree, add_xml_child, UnixLex


log = getLogger(__name__)


class LinuxMenu(Menu):
    """
    Menus in Linux are governed by the freedesktop.org standards,
    spec'd here https://specifications.freedesktop.org/menu-spec/menu-spec-latest.html

    menuinst will populate the relevant XML config and create a .directory entry
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.mode == "system":
            self.config_directory = Path("/etc/xdg/")
            self.data_directory = Path("/usr/share")
        else:
            self.config_directory = Path(
                os.environ.get("XDG_CONFIG_HOME", "~/.config")
            ).expanduser()
            self.data_directory = Path(
                os.environ.get("XDG_DATA_HOME", "~/.local/share")
            ).expanduser()

        # XML Config paths
        self.system_menu_config_location = Path("/etc/xdg/") / "menus" / "applications.menu"
        self.menu_config_location = self.config_directory / "menus" / "applications.menu"
        # .desktop / .directory paths
        self.directory_entry_location = (
            self.data_directory
            / "desktop-directories"
            / f"{self.render(self.name, slug=True)}.directory"
        )
        self.desktop_entries_location = self.data_directory / "applications"

    def create(self):
        self._ensure_directories_exist()
        path = self._write_directory_entry()
        if self._is_valid_menu_file() and self._has_this_menu():
            return (path,)
        self._ensure_menu_file()
        self._add_this_menu()
        return (path,)

    def remove(self):
        self.directory_entry_location.unlink()
        for fn in os.listdir(self.menu_entries_location):
            if fn.startswith(f"{self.render(self.name, slug=True)}_"):
                # found one shortcut, so don't remove the name from menu
                return (self.directory_entry_location,)
        self._remove_this_menu()
        return (self.directory_entry_location,)

    @property
    def placeholders(self):
        placeholders = super().placeholders
        placeholders["SP_DIR"] = str(self._site_packages())
        return placeholders

    def _ensure_directories_exist(self):
        paths = [
            self.config_directory / "menus",
            self.data_directory / "desktop-directories",
            self.data_directory / "applications",
        ]
        for path in paths:
            log.debug("Ensuring path %s exists", path)
            path.mkdir(parents=True, exist_ok=True)

    #
    # .directory stuff methods
    #

    def _write_directory_entry(self):
        lines = [
            "[Desktop Entry]",
            "Type=Directory",
            "Encoding=UTF-8",
            f"Name={self.render(self.name)}",
        ]
        log.debug("Writing directory entry at %s", self.directory_entry_location)
        with open(self.directory_entry_location, "w") as f:
            f.write("\n".join(lines))

        return self.directory_entry_location

    #
    # XML config stuff methods
    #

    def _remove_this_menu(self):
        log.debug("Editing %s to remove %s config", self.menu_config_location, self.name)
        tree = XMLTree.parse(self.menu_config_location)
        root = tree.getroot()
        for elt in root.findall("Menu"):
            if elt.find("Name").text == self.name:
                root.remove(elt)
        self._write_menu_file(tree)

    def _has_this_menu(self):
        root = XMLTree.parse(self.menu_config_location).getroot()
        return any(e.text == self.name for e in root.findall("Menu/Name"))

    def _add_this_menu(self):
        log.debug("Editing %s to add %s config", self.menu_config_location, self.name)
        tree = XMLTree.parse(self.menu_config_location)
        root = tree.getroot()
        menu_elt = add_xml_child(root, "Menu")
        add_xml_child(menu_elt, "Name", self.name)
        add_xml_child(menu_elt, "Directory", f"{self.render(self.name, slug=True)}.directory")
        inc_elt = add_xml_child(menu_elt, "Include")
        add_xml_child(inc_elt, "Category", self.name)
        self._write_menu_file(tree)

    def _is_valid_menu_file(self):
        try:
            root = XMLTree.parse(self.menu_config_location).getroot()
            return root is not None and root.tag == "Menu"
        except Exception:
            return False

    def _write_menu_file(self, tree):
        log.debug("Writing %s", self.menu_config_location)
        indent_xml_tree(tree.getroot())  # inplace!
        with open(self.menu_config_location, "wb") as f:
            f.write(b'<!DOCTYPE Menu PUBLIC "-//freedesktop//DTD Menu 1.0//EN"\n')
            f.write(b' "http://standards.freedesktop.org/menu-spec/menu-1.0.dtd">\n')
            tree.write(f)
            f.write(b"\n")

    def _ensure_menu_file(self):
        # ensure any existing version is a file
        if self.menu_config_location.exists() and not self.menu_config_location.is_file():
            raise RuntimeError(f"Menu config location {self.menu_config_location} is not a file!")
            # shutil.rmtree(self.menu_config_location)

        # ensure any existing file is actually a menu file
        if self.menu_config_location.is_file():
            # make a backup of the menu file to be edited
            cur_time = time.strftime("%Y-%m-%d_%Hh%Mm%S")
            backup_menu_file = f"{self.menu_config_location}.{cur_time}"
            shutil.copyfile(self.menu_config_location, backup_menu_file)

            if not self._is_valid_menu_file():
                os.remove(self.menu_config_location)
        else:
            self._new_menu_file()

    def _new_menu_file(self):
        log.debug("Creating %s", self.menu_config_location)
        with open(self.menu_config_location, "w") as f:
            f.write("<Menu><Name>Applications</Name>")
            if self.mode == "user":
                f.write(f'<MergeFile type="parent">{self.system_menu_config_location}</MergeFile>')
            f.write("</Menu>\n")

    def _paths(self):
        return (self.directory_entry_location,)


class LinuxMenuItem(MenuItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        menu_prefix = self.menu.render(self.menu.name, slug=True)
        # TODO: filename should conform to D-Bus well known name conventions
        # https://specifications.freedesktop.org/desktop-entry-spec/latest/ar01s02.html
        filename = f"{menu_prefix}_{self.render('name', slug=True)}.desktop"
        self.location = self.menu.desktop_entries_location / filename

    def create(self):
        log.debug("Creating %s", self.location)
        self._write_desktop_file()
        return self._paths()

    def remove(self):
        paths = self._paths()
        for path in paths:
            log.debug("Removing %s", path)
            path.unlink()
        return paths

    def _command(self):
        cmd = ""
        if self.metadata.activate:
            conda_exe = self.menu.conda_exe
            if self.menu._is_micromamba(conda_exe):
                activate = "shell activate"
            else:
                activate = "shell.bash activate"
            cmd = f'eval "$("{conda_exe}" {activate} "{self.menu.prefix}")" && '
        cmd += " ".join(UnixLex.quote_args(self.render("command")))
        cmd = f"bash -c '{cmd}'"
        return cmd

    def _write_desktop_file(self):
        lines = [
            "[Desktop Entry]",
            "Type=Application",
            "Encoding=UTF-8",
            f'Name={self.render("name")}',
            f"Exec={self._command()}",
            f'Terminal={self.render("terminal")}',
        ]

        icon = self.render("icon")
        if icon:
            lines.append(f'Icon={self.render("icon")}')

        description = self.render("description")
        if description:
            lines.append(f'Comment={self.render("description")}')

        working_dir = self.render("working_dir")
        if working_dir:
            Path(working_dir).mkdir(parents=True, exist_ok=True)
            lines.append(f"Path={working_dir}")

        for key in MenuInstSchema.MenuItem.Platforms.Linux.__fields__:
            if key in MenuInstSchema.MenuItem.__fields__:
                continue
            value = self.render(key)
            if value is None:
                continue
            if isinstance(value, bool):
                value = str(value).lower()
            elif isinstance(value, (list, tuple)):
                value = ";".join(value) + ";"
            lines.append(f"{key}={value}")

        with open(self.location, "w") as f:
            f.write("\n".join(lines))
            f.write("\n")

    def _paths(self) -> Iterable[Union[str, os.PathLike]]:
        return (self.location,)
