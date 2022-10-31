"""
"""
from logging import getLogger
from pathlib import Path
from typing import Tuple
import importlib.resources
import os
import platform
import plistlib
import shutil

from .base import Menu, MenuItem, menuitem_defaults
from ..utils import UnixLex


log = getLogger(__name__)


class MacOSMenu(Menu):
    def create(self):
        return self._paths()

    def remove(self):
        return self._paths()

    @property
    def placeholders(self):
        placeholders = super().placeholders
        placeholders.update(
            {
                "SP_DIR": str(self._site_packages()),
                "ICON_EXT": "icns",
                "PYTHONAPP": str(self.prefix / "python.app" / "Contents" / "MacOS" / "python"),
            }
        )
        return placeholders

    def _paths(self):
        return ()


class MacOSMenuItem(MenuItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        name = f"{self.render('name')}.app"

        _test_tmpdir = os.environ.get("MENUINST_TEST_TMPDIR")
        if _test_tmpdir:
            base = Path(_test_tmpdir)
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
        self._write_launcher()
        self._write_script()
        return (self.location,)

    def remove(self) -> Tuple[Path]:
        log.debug("Removing %s", self.location)
        shutil.rmtree(self.location, ignore_errors=True)
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
        name = self.render("name")
        slugname = self.render("name", slug=True)
        pl = {
            "CFBundleName": name,
            "CFBundleDisplayName": name,
            "CFBundleExecutable": slugname,
            "CFBundleGetInfoString": f"{slugname}-1.0.0",
            "CFBundleIdentifier": f"com.{slugname}",
            "CFBundlePackageType": "APPL",
            "CFBundleVersion": "1.0.0",
            "CFBundleShortVersionString": "1.0.0",
        }

        # Override defaults with (potentially) user provided values
        for key in menuitem_defaults["platforms"]["osx"]:
            if key in menuitem_defaults:
                continue
            value = self.render(key)
            if value is None:
                continue
            if key == "CFBundleVersion":
                # setting the version also changes these two values
                pl["CFBundleShortVersionString"] = value
                pl["CFBundleGetInfoString"] = f"{slugname}-{value}"
            pl[key] = value

        icon = self.render("icon")
        if icon:
            pl["CFBundleIconFile"] = Path(icon).name

        with open(self.location / "Contents" / "Info.plist", "wb") as f:
            plistlib.dump(pl, f)

    def _command(self):
        lines = ["#!/bin/sh"]
        if self.render("terminal"):
            # FIXME: Terminal launching will miss the arguments;
            # there's no easy way to pass them!
            lines.extend(
                [
                    'if [ "${__CFBundleIdentifier:-}" != "com.apple.Terminal" ]; then',
                    '    open -b com.apple.terminal "$0"',
                    '    exit $?',
                    'fi',
                ]
            )

        working_dir = self.render("working_dir")
        if working_dir:
            Path(working_dir).mkdir(parents=True, exist_ok=True)
            lines.append(f'cd "{working_dir}"')

        if self.metadata["activate"]:
            conda_exe = self.menu.conda_exe
            if self.menu._is_micromamba(conda_exe):
                activate = "shell activate"
            else:
                activate = "shell.bash activate"
            lines.append(f'eval "$("{conda_exe}" {activate} "{self.menu.prefix}")"')

        lines.append(" ".join(UnixLex.quote_args(self.render("command"))))

        return "\n".join(lines)

    def _write_launcher(self, launcher_path=None):
        if launcher_path is None:
            launcher_path = self._default_launcher_path()
        shutil.copy(self._find_launcher(), launcher_path)
        os.chmod(launcher_path, 0o755)
        return launcher_path

    def _write_script(self, script_path=None):
        if script_path is None:
            script_path = self._default_launcher_path(suffix="-script")
        with open(script_path, "w") as f:
            f.write(self._command())
        os.chmod(script_path, 0o755)
        return script_path

    def _paths(self):
        return (self.location,)

    def _find_launcher(self):
        launcher_name = f"osx_launcher_{platform.machine()}"
        launcher_path = importlib.resources.files("menuinst") / "data" / launcher_name
        if launcher_path.is_file() and os.access(launcher_path, os.X_OK):
            return launcher_path
        raise ValueError(f"Could not find executable launcher for {platform.machine()}")

    def _default_launcher_path(self, suffix=""):
        name = self.render("name", slug=True)
        return self.location / "Contents" / "MacOS" / f'{name}{suffix}'
