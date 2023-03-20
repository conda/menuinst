"""
"""
import os
import platform
import plistlib
import shutil
import sys
from hashlib import sha1
from logging import getLogger
from pathlib import Path
from subprocess import CalledProcessError, check_call, run
from textwrap import dedent
from typing import Dict, Optional, Tuple

from .. import data as _menuinst_data
from ..utils import UnixLex
from .base import Menu, MenuItem, menuitem_defaults

log = getLogger(__name__)


class MacOSMenu(Menu):
    def create(self) -> Tuple:
        return self._paths()

    def remove(self) -> Tuple:
        return self._paths()

    @property
    def placeholders(self) -> Dict[str, str]:
        placeholders = super().placeholders
        placeholders.update(
            {
                "SP_DIR": str(self._site_packages()),
                "ICON_EXT": "icns",
                "PYTHONAPP": str(self.prefix / "python.app" / "Contents" / "MacOS" / "python"),
            }
        )
        return placeholders

    def _paths(self) -> Tuple:
        return ()


class MacOSMenuItem(MenuItem):

    @property
    def location(self) -> Path:
        "Path to the .app directory defining the menu item"
        return self._base_location() / "Applications" / self._bundle_name

    @property
    def _bundle_name(self) -> str:
        return f"{self.render_key('name', extra={})}.app"

    @property
    def _nested_location(self) -> Path:
        "Path to the nested .app directory defining the menu item main app"
        return self.location / "Contents" / "Resources" / self._bundle_name

    def _base_location(self) -> Path:
        if self.menu.mode == "user":
            return Path("~").expanduser()
        return Path("/")

    def _precreate(self):
        super()._precreate()
        for src, dest in (self.metadata["link_in_bundle"] or {}).items():
            rendered_dest: Path = (self.location / self.render(dest)).resolve()
            # if not rendered_dest.is_relative_to(self.location):  # FUTURE: Only for 3.9+
            if not str(rendered_dest).startswith(str(self.location)):
                raise ValueError(
                    "'link_in_bundle' destinations MUST be created "
                    f"inside the .app bundle ({self.location}), but it points to '{rendered_dest}."
                )
            rendered_dest.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(self.render(src), rendered_dest)

    def create(self) -> Tuple[Path]:
        log.debug("Creating %s", self.location)
        self._create_application_tree()
        self._precreate()
        self._copy_icon()
        self._write_pkginfo()
        self._write_plistinfo()
        self._write_appkit_launcher()
        self._write_launcher()
        self._write_script()
        self._write_url_handler()
        self._maybe_register_url()
        self._sign_with_entitlements()
        return (self.location,)

    def remove(self) -> Tuple[Path]:
        log.debug("Removing %s", self.location)
        self._maybe_register_url(register=False)
        shutil.rmtree(self.location, ignore_errors=True)
        return (self.location,)

    def _create_application_tree(self) -> Tuple[Path]:
        paths = [
            self.location / "Contents" / "Resources",
            self.location / "Contents" / "MacOS",
        ]
        if self._needs_appkit_launcher:
            paths += [
                self._nested_location / "Contents" / "Resources",
                self._nested_location / "Contents" / "MacOS",
            ]
        for path in paths:
            path.mkdir(parents=True, exist_ok=False)
        return tuple(paths)

    def _copy_icon(self):
        icon = self.render_key("icon")
        if icon:
            shutil.copy(icon, self.location / "Contents" / "Resources")
            if self._needs_appkit_launcher:
                shutil.copy(icon, self._nested_location / "Contents" / "Resources")

    def _write_pkginfo(self):
        app_bundles = [self.location]
        if self._needs_appkit_launcher:
            app_bundles.append(self._nested_location)
        for app in app_bundles:
            with open(app / "Contents" / "PkgInfo", "w") as f:
                f.write(f"APPL{self.render_key('name', slug=True)[:8]}")

    def _write_plistinfo(self):
        name = self.render_key("name")
        slugname = self.render_key("name", slug=True)
        if len(slugname) > 16:
            shortname = slugname[:10] + sha1(slugname.encode()).hexdigest()[:6]
        else:
            shortname = slugname
        pl = {
            "CFBundleName": shortname,
            "CFBundleDisplayName": name,
            "CFBundleExecutable": slugname,
            "CFBundleGetInfoString": f"{slugname}-1.0.0",
            "CFBundleIdentifier": f"com.{slugname}",
            "CFBundlePackageType": "APPL",
            "CFBundleVersion": "1.0.0",
            "CFBundleShortVersionString": "1.0.0",
        }

        icon = self.render_key("icon")
        if icon:
            pl["CFBundleIconFile"] = Path(icon).name

        if self._needs_appkit_launcher:
            # write only the basic plist info into the nested bundle
            with open(self._nested_location / "Contents" / "Info.plist", "wb") as f:
                plistlib.dump(pl, f)
            # the *outer* bundle is background-only and needs a different ID
            pl["LSBackgroundOnly"] = True
            pl["CFBundleIdentifier"] = f"com.{slugname}-appkit-launcher"

        # Override defaults with (potentially) user provided values
        ignore_keys = (*menuitem_defaults, "entitlements", "link_in_bundle")
        for key in menuitem_defaults["platforms"]["osx"]:
            if key in ignore_keys:
                continue
            value = self.render_key(key)
            if value is None:
                continue
            if key == "CFBundleVersion":
                # setting the version also changes these two values
                pl["CFBundleShortVersionString"] = value
                pl["CFBundleGetInfoString"] = f"{slugname}-{value}"
            pl[key] = value
        with open(self.location / "Contents" / "Info.plist", "wb") as f:
            plistlib.dump(pl, f)

    def _command(self) -> str:
        lines = ["#!/bin/sh"]
        if self.render_key("terminal"):
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

        working_dir = self.render_key("working_dir")
        if working_dir:
            Path(working_dir).mkdir(parents=True, exist_ok=True)
            lines.append(f'cd "{working_dir}"')

        precommand = self.render_key("precommand")
        if precommand:
            lines.append(precommand)

        if self.metadata["activate"]:
            conda_exe = self.menu.conda_exe
            if self.menu._is_micromamba(conda_exe):
                activate = "shell activate"
            else:
                activate = "shell.bash activate"
            lines.append(f'eval "$("{conda_exe}" {activate} "{self.menu.prefix}")"')

        lines.append(" ".join(UnixLex.quote_args(self.render_key("command"))))

        return "\n".join(lines)

    def _write_appkit_launcher(self, launcher_path: Optional[os.PathLike] = None) -> os.PathLike:
        if launcher_path is None:
            launcher_path = self._default_appkit_launcher_path()
        shutil.copy(self._find_appkit_launcher(), launcher_path)
        os.chmod(launcher_path, 0o755)
        return launcher_path

    def _write_launcher(self, launcher_path: Optional[os.PathLike] = None) -> os.PathLike:
        if launcher_path is None:
            launcher_path = self._default_launcher_path()
        shutil.copy(self._find_launcher(), launcher_path)
        os.chmod(launcher_path, 0o755)
        return launcher_path

    def _write_script(self, script_path: Optional[os.PathLike] = None) -> os.PathLike:
        if script_path is None:
            script_path = self._default_launcher_path(suffix="-script")
        with open(script_path, "w") as f:
            f.write(self._command())
        os.chmod(script_path, 0o755)
        return script_path

    def _write_url_handler(self, script_path: Optional[os.PathLike] = None) -> os.PathLike:
        if not self._needs_appkit_launcher:
            return
        url_handler_logic = self.render_key("url_handler")
        if url_handler_logic is None:
            return
        if script_path is None:
            script_path = self.location / "Contents" / "Resources" / "handle-url"
        with open(script_path, "w") as f:
            f.write(
                dedent(
                    f"""
                    #!/bin/bash
                    {url_handler_logic}
                    """
                ).lstrip()
            )
        os.chmod(script_path, 0o755)
        return script_path

    def _paths(self) -> Tuple[os.PathLike]:
        return (self.location,)

    def _find_appkit_launcher(self) -> Path:
        launcher_name = f"appkit_launcher_{platform.machine()}"
        for datapath in _menuinst_data.__path__:
            launcher_path = Path(datapath) / launcher_name
            if launcher_path.is_file() and os.access(launcher_path, os.X_OK):
                return launcher_path
        raise ValueError(f"Could not find executable launcher for {platform.machine()}")

    def _find_launcher(self) -> Path:
        launcher_name = f"osx_launcher_{platform.machine()}"
        for datapath in _menuinst_data.__path__:
            launcher_path = Path(datapath) / launcher_name
            if launcher_path.is_file() and os.access(launcher_path, os.X_OK):
                return launcher_path
        raise ValueError(f"Could not find executable launcher for {platform.machine()}")

    def _default_appkit_launcher_path(self, suffix: str = "") -> Path:
        name = self.render_key("name", slug=True)
        return self.location / "Contents" / "MacOS" / f'{name}{suffix}'

    def _default_launcher_path(self, suffix: str = "") -> Path:
        name = self.render_key("name", slug=True)
        if self._needs_appkit_launcher:
            return self._nested_location / "Contents" / "MacOS" / f'{name}{suffix}'
        return self.location / "Contents" / "MacOS" / f'{name}{suffix}'

    def _maybe_register_url(self, register=True):
        if not self._needs_appkit_launcher:
            return
        # register the URL scheme with `lsregister`
        try:
            unregister = () if register else ("-u",)
            _lsregister("-R", *unregister, str(self.location))
        except CalledProcessError as exc:
            log.debug("Could not (un)register URL scheme", exc_info=exc)

    def _sign_with_entitlements(self):
        "Self-sign shortcut to apply required entitlements"
        entitlement_keys = self.render_key("entitlements")
        if not entitlement_keys:
            return
        slugname = self.render_key("name", slug=True)
        plist = {key: True for key in entitlement_keys}
        entitlements_path = self.location / "Contents" / "Entitlements.plist"
        with open(entitlements_path, "wb") as f:
            plistlib.dump(plist, f)
        check_call(
            [
                # hardcode to system location to avoid accidental clobber in PATH
                "/usr/bin/codesign",
                "--verbose",
                "--sign",
                "-",
                "--prefix",
                f"com.{slugname}",
                "--options",
                "runtime",
                "--force",
                "--deep",
                "--entitlements",
                entitlements_path,
                self.location
            ]
        )

    @property
    def _needs_appkit_launcher(self) -> bool:
        if self.metadata.get("CFBundleURLTypes"):
            return True
        return False

def _lsregister(*args):
    exe = (
        "/System/Library/Frameworks/CoreServices.framework"
        "/Frameworks/LaunchServices.framework/Support/lsregister"
    )
    if not os.path.exists(exe):
        return
    p = run([exe, *args], capture_output=True, text=True)
    if p.returncode:
        log.debug("Command %s failed with error code %s", p.args, p.returncode)
        log.debug(p.stdout)
        log.debug(p.stderr, file=sys.stderr)
        p.check_returncode()
    return p
