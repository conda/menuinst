"""
"""
import os
from pathlib import Path
import shutil
import xml.etree.ElementTree as XMLTree
import time
from logging import getLogger
from typing import Tuple, Iterable, Dict

from .base import Menu, MenuItem, menuitem_defaults
from ..utils import indent_xml_tree, add_xml_child, UnixLex, unlink


log = getLogger(__name__)


class LinuxMenu(Menu):
    """
    Menus in Linux are governed by the freedesktop.org standards,
    spec'd here https://specifications.freedesktop.org/menu-spec/menu-spec-latest.html

    menuinst will populate the relevant XML config and create a .directory entry
    """
    _system_config_directory = Path("/etc/xdg/")
    _system_data_directory =  Path("/usr/share")
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.mode == "system":
            self.config_directory = self._system_config_directory
            self.data_directory =self._system_data_directory
        else:
            self.config_directory = Path(
                os.environ.get("XDG_CONFIG_HOME", "~/.config")
            ).expanduser()
            self.data_directory = Path(
                os.environ.get("XDG_DATA_HOME", "~/.local/share")
            ).expanduser()

        # XML Config paths
        self.system_menu_config_location = self._system_config_directory / "menus" / "applications.menu"
        self.menu_config_location = self.config_directory / "menus" / "applications.menu"
        # .desktop / .directory paths
        self.directory_entry_location = (
            self.data_directory
            / "desktop-directories"
            / f"{self.render(self.name, slug=True)}.directory"
        )
        self.desktop_entries_location = self.data_directory / "applications"

    def create(self) -> Tuple[os.PathLike]:
        self._ensure_directories_exist()
        path = self._write_directory_entry()
        if self._is_valid_menu_file() and self._has_this_menu():
            return (path,)
        self._ensure_menu_file()
        self._add_this_menu()
        return (path,)

    def remove(self) -> Tuple[os.PathLike]:
        unlink(self.directory_entry_location, missing_ok=True)
        for fn in os.listdir(self.desktop_entries_location):
            if fn.startswith(f"{self.render(self.name, slug=True)}_"):
                # found one shortcut, so don't remove the name from menu
                return (self.directory_entry_location,)
        self._remove_this_menu()
        return (self.directory_entry_location,)

    @property
    def placeholders(self) -> Dict[str, str]:
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

    def _write_directory_entry(self) -> str:
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

    def _has_this_menu(self) -> bool:
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

    def _is_valid_menu_file(self) -> bool:
        try:
            root = XMLTree.parse(self.menu_config_location).getroot()
            return root is not None and root.tag == "Menu"
        except Exception:
            return False

    def _write_menu_file(self, tree: XMLTree):
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

    def _paths(self) -> Tuple[str]:
        return (self.directory_entry_location,)


class LinuxMenuItem(MenuItem):
    @property
    def location(self) -> Path:
        menu_prefix = self.render(self.menu.name, slug=True, extra={})
        # TODO: filename should conform to D-Bus well known name conventions
        # https://specifications.freedesktop.org/desktop-entry-spec/latest/ar01s02.html
        filename = f"{menu_prefix}_{self.render_key('name', slug=True, extra={})}.desktop"
        return self.menu.desktop_entries_location / filename

    def create(self) -> Iterable[os.PathLike]:
        log.debug("Creating %s", self.location)
        self._precreate()
        self._write_desktop_file()
        return self._paths()

    def remove(self) -> Iterable[os.PathLike]:
        paths = self._paths()
        for path in paths:
            log.debug("Removing %s", path)
            unlink(path, missing_ok=True)
        return paths

    def _command(self) -> str:
        parts = []
        precommand = self.render_key("precommand")
        if precommand:
            parts.append(precommand)
        if self.metadata["activate"]:
            conda_exe = self.menu.conda_exe
            if self.menu._is_micromamba(conda_exe):
                activate = "shell activate"
            else:
                activate = "shell.bash activate"
            parts.append(f'eval "$("{conda_exe}" {activate} "{self.menu.prefix}")"')
        parts.append(" ".join(UnixLex.quote_args(self.render_key("command"))))
        return f"bash -c '{' && '.join(parts)}'"

    def _write_desktop_file(self):
        lines = [
            "[Desktop Entry]",
            "Type=Application",
            "Encoding=UTF-8",
            f'Name={self.render_key("name")}',
            f"Exec={self._command()}",
            f'Terminal={str(self.render_key("terminal")).lower()}',
        ]

        icon = self.render_key("icon")
        if icon:
            lines.append(f'Icon={self.render_key("icon")}')

        description = self.render_key("description")
        if description:
            lines.append(f'Comment={self.render_key("description")}')

        working_dir = self.render_key("working_dir")
        if working_dir:
            Path(working_dir).mkdir(parents=True, exist_ok=True)
            lines.append(f"Path={working_dir}")

        for key in menuitem_defaults["platforms"]["linux"]:
            if key in menuitem_defaults:
                continue
            value = self.render_key(key)
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

    def _paths(self) -> Iterable[os.PathLike]:
        return (self.location,)
