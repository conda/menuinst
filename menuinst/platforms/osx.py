"""
"""
import shutil
from pathlib import Path
import plistlib
import os
from typing import Tuple
from tempfile import mkdtemp
from logging import getLogger

from .base import Menu, MenuItem
from ..utils import UnixLex


log = getLogger(__name__)


class MacOSMenu(Menu):
    def create(self):
        pass

    def remove(self):
        pass

    @property
    def placeholders(self):
        placeholders = super().placeholders
        placeholders.update(
            {
                "SP_DIR": str(self._site_packages()),
                "ICON_EXT": "icns",
                "PYTHONAPP": str(
                    self.prefix / "python.app" / "Contents" / "MacOS" / "python"
                ),
            }
        )
        return placeholders

    def _paths(self):
        return ()

class MacOSMenuItem(MenuItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        name = f"{self.render('name')}.app"
        if os.environ.get("PYTEST_IN_USE"):
            base = Path(mkdtemp(prefix="menuinst-pytest-"))
        elif self.menu.mode == "user":
            base = Path("~").expanduser()
        else:
            base = Path("/")

        self.location = base / "Applications" / name

    def create(self) -> Tuple[Path]:
        log.debug("Creating %s", self.location)
        self._create_application_tree()
        icon = self.render("icon")
        if icon:
            shutil.copy(self.render("icon"), self.location / "Contents" / "Resources")
        self._write_pkginfo()
        self._write_plistinfo()
        self._write_script()
        return (self.location,)

    def remove(self) -> Tuple[Path]:
        log.debug("Removing %s", self.location)
        shutil.rmtree(self.location)
        return (self.location,)

    def _create_application_tree(self):
        paths = [
            self.location / "Contents" / "Resources",
            self.location / "Contents" / "MacOS",
        ]
        for path in paths:
            path.mkdir(parents=True, exist_ok=False)
        return paths

    def _write_pkginfo(self):
        with open(self.location / "Contents" / "PkgInfo", "w") as f:
            f.write(f"APPL{self.render('name', slug=True)[:8]}")

    def _write_plistinfo(self):
        name = self.render("name", slug=True)
        pl = {
            "CFBundleExecutable": name,
            "CFBundleGetInfoString": f"{name}-1.0.0",
            "CFBundleIdentifier": f"com.{name}",
            "CFBundlePackageType": "APPL",
            "CFBundleVersion": "1.0.0",
            "CFBundleShortVersionString": "1.0.0",
        }
        icon = self.render("icon")
        if icon:
            pl["CFBundleIconFile"] = Path(icon).name

        with open(self.location / "Contents" / "Info.plist", "wb") as f:
            plistlib.dump(pl, f)

    def _command(self):
        lines = ["#!/bin/bash"]

        working_dir = self.render("working_dir")
        if working_dir:
            Path(working_dir).mkdir(parents=True, exist_ok=True)
            lines.append(f'cd "{working_dir}"')

        if self.metadata.activate:
            conda_exe = self.menu.conda_exe
            if self.menu._is_micromamba(conda_exe):
                activate = "shell activate"
            else:
                activate = "shell.bash activate"
            lines.append(
                f"eval $(\"{conda_exe}\" {activate} \"{self.menu.prefix}\")"
            )

        lines.append(" ".join(UnixLex.quote_args(self.render("command"))))

        return "\n".join(lines)

    def _write_script(self, script_path=None):
        if script_path is None:
            script_path = self.location / "Contents" / "MacOS" / self.render("name", slug=True)
        with open(script_path, "w") as f:
            f.write(self._command())
        os.chmod(script_path, 0o755)
        return script_path

    def _paths(self):
        return (self.location,)
