"""
"""
import os
import sys
from typing import Union, List, Iterable
from pathlib import Path
from subprocess import check_output
from logging import getLogger

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from ..schema import MenuInstSchema
from ..utils import slugify

log = getLogger(__name__)

class Menu:
    def __init__(
        self,
        name: str,
        prefix: str = sys.prefix,
        base_prefix: str = sys.prefix,
        mode: Union[Literal["user"], Literal["system"]] = "user",
    ):
        assert mode in ("user", "system"), f"`mode` must be either `user` or `system`"
        self.mode = mode
        self.name = name
        self.prefix = Path(prefix)
        self.base_prefix = Path(base_prefix)

        self.env_name = None

    def create(self) -> List[Path]:
        raise NotImplementedError

    def remove(self) -> List[Path]:
        raise NotImplementedError

    def render(self, value: Union[str, None], slug: bool = False):
        if value is None:
            return
        for placeholder, replacement in self.placeholders.items():
            value = value.replace("{{ " + placeholder + " }}", replacement)
        if slug:
            value = slugify(value)
        return value

    @property
    def placeholders(self):
        return {
            "BASE_PREFIX": str(self.base_prefix),
            "DISTRIBUTION_NAME": self.base_prefix.name,
            "BASE_PYTHON": str(self.base_prefix / "bin" / "python"),
            "PREFIX": str(self.prefix),
            "ENV_NAME": self.prefix.name,
            "PYTHON": str(self.prefix / "bin" / "python"),
            "MENU_DIR": str(self.prefix / "Menu"),
            "BIN_DIR": str(self.prefix / "bin"),
            "PY_VER": "N.A",
            "HOME": os.path.expanduser("~"),
            "ICON_EXT": "png",
        }

    def _conda_exe_path_candidates(self):
        return (
            self.base_prefix / "_conda.exe",
            Path(os.environ.get("CONDA_EXE", "/oops/a_file_that_does_not_exist")),
            self.base_prefix / "condabin" / "conda",
            self.base_prefix / "bin" / "conda",
            Path(os.environ.get("MAMBA_EXE", "/oops/a_file_that_does_not_exist")),
            self.base_prefix / "condabin" / "micromamba",
            self.base_prefix / "bin" / "micromamba",
        )

    @property
    def conda_exe(self):
        if sys.executable.endswith("_conda.exe"):
            # This is the case with `constructor` calls
            return Path(sys.executable)

        for path in self._conda_exe_path_candidates():
            if path.is_file():
                return path

        return Path("conda")

    def _is_micromamba(self, exe: Path):
        if "micromamba" in exe.name:
            return True
        if exe.name == "_conda.exe":
            out = check_output([str(exe), "info"], universal_newlines=True)
            return "micromamba version" in out
        return False

    def _site_packages(self, prefix=None) -> Path:
        """
        Locate the python site-packages location on unix systems
        """
        if prefix is None:
            prefix = self.prefix
        lib = Path(prefix) / "lib"
        lib_python = next((p for p in lib.glob("python*") if p.is_dir()), lib / "pythonN.A")
        return lib_python / "site-packages"

    def _paths(self) -> Iterable[Union[str, os.PathLike]]:
        """
        This method should return the paths created by the menu
        so they can be removed upon uninstallation
        """
        raise NotImplementedError


class MenuItem:
    def __init__(self, menu: Menu, metadata: MenuInstSchema.MenuItem):
        self.menu = menu
        self._data = metadata
        self.metadata = self._merge_for_platform(self._data)

    def create(self) -> List[Path]:
        raise NotImplementedError

    def remove(self) -> List[Path]:
        raise NotImplementedError

    def render(self, key: str, slug=False):
        value = self.metadata.get(key)
        if value in (None, True, False):
            return value
        if isinstance(value, str):
            return self.menu.render(value, slug=slug)
        return [self.menu.render(item, slug=slug) for item in value]

    def _paths(self) -> Iterable[Union[str, os.PathLike]]:
        """
        This method should return the paths created by the item
        so they can be removed upon uninstallation
        """
        raise NotImplementedError

    @staticmethod
    def _merge_for_platform(data, platform=sys.platform):
        """
        Merge platform keys with global keys, overwriting if needed.
        """
        platform = platform_key(platform)
        data_copy = data.copy()
        all_platforms = data_copy.pop("platforms", None)
        if all_platforms:
            platform_options = all_platforms.pop(platform)
            if platform_options:
                for key, value in platform_options.items():
                    if key not in data_copy:
                        # bring missing keys, since they are platform specific
                        data_copy[key] = value
                    elif value is not None:
                        # if the key was in global, it was not platform specific
                        # this is an override and we only do so if is not None
                        log.debug("Platform value %s=%s overrides global value", key, value)
                        data_copy[key] = value

        data["platforms"] = [
            key for key, value in data_copy["platforms"].items()
            if value is not None
        ]
        return data

    def enabled_for_platform(self, platform=sys.platform):
        platform = platform_key(platform)
        return self._data["platforms"].get(platform) is not None


def platform_key(platform=sys.platform):
    if platform == "win32":
        return "win"
    if platform == "darwin":
        return "osx"
    if platform.startswith("linux"):
        return "linux"

    raise ValueError(f"Platform {platform} is not supported")
