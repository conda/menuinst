"""
"""
import os
import sys
from typing import Union, List, Iterable, Literal, Dict, Any, Optional, Mapping
from pathlib import Path
from subprocess import check_output, run
from logging import getLogger
from copy import deepcopy
from tempfile import NamedTemporaryFile
import json

from ..utils import slugify, data_path, deep_update, DEFAULT_PREFIX, DEFAULT_BASE_PREFIX

log = getLogger(__name__)


class Menu:
    def __init__(
        self,
        name: str,
        prefix: str = DEFAULT_PREFIX,
        base_prefix: str = DEFAULT_BASE_PREFIX,
        mode: Union[Literal["user"], Literal["system"]] = "user",
    ):
        assert mode in ("user", "system"), f"mode={mode} must be `user` or `system`"
        self.mode = mode
        self.name = name
        self.prefix = Path(prefix)
        self.base_prefix = Path(base_prefix)

        self.env_name = None

    def create(self) -> List[Path]:
        raise NotImplementedError

    def remove(self) -> List[Path]:
        raise NotImplementedError

    def render(self, value: Any, slug: bool = False, extra: Dict = None) -> Any:
        if not hasattr(value, "replace"):
            return value
        if extra:
            placeholders = {**self.placeholders, **extra}
        else:
            placeholders = self.placeholders
        for placeholder, replacement in placeholders.items():
            value = value.replace("{{ " + placeholder + " }}", replacement)
        if slug:
            value = slugify(value)
        return value

    @property
    def placeholders(self) -> Dict[str, str]:
        """
        Additional placeholders added at runtime:
        - MENU_ITEM_LOCATION -> *MenuItem().location

        Subclasses may extend this dictionary!
        """
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

    def _conda_exe_path_candidates(self) -> Dict[str, str]:
        return (
            self.base_prefix / "_conda.exe",
            self.base_prefix / "conda.exe",
            Path(os.environ.get("CONDA_EXE", "/oops/a_file_that_does_not_exist")),
            self.base_prefix / "condabin" / "conda",
            self.base_prefix / "bin" / "conda",
            Path(os.environ.get("MAMBA_EXE", "/oops/a_file_that_does_not_exist")),
            self.base_prefix / "condabin" / "micromamba",
            self.base_prefix / "bin" / "micromamba",
        )

    @property
    def conda_exe(self) -> Path:
        if sys.executable.endswith("conda.exe"):
            # This is the case with `constructor` calls
            return Path(sys.executable)

        for path in self._conda_exe_path_candidates():
            if path.is_file():
                return path

        return Path("conda")

    def _is_micromamba(self, exe: Path) -> bool:
        if "micromamba" in exe.name:
            return True
        if exe.name in ("conda.exe", "_conda.exe"):
            out = check_output([str(exe), "info"], universal_newlines=True)
            return "micromamba version" in out
        return False

    def _site_packages(self, prefix=None) -> Path:
        """
        Locate the python site-packages location on unix systems
        """
        if os.name == "nt":
            raise NotImplementedError
        if prefix is None:
            prefix = self.prefix
        lib = Path(prefix) / "lib"
        lib_python = next((p for p in lib.glob("python*") if p.is_dir()), lib / "pythonN.A")
        return lib_python / "site-packages"

    def _paths(self) -> Iterable[os.PathLike]:
        """
        This method should return the paths created by the menu
        so they can be removed upon uninstallation
        """
        raise NotImplementedError


class MenuItem:
    def __init__(self, menu: Menu, metadata: dict):
        self.menu = menu
        self._data = self._initialize_on_defaults(metadata)
        self.metadata = self._flatten_for_platform(self._data)

    def create(self) -> List[Path]:
        raise NotImplementedError

    def remove(self) -> List[Path]:
        raise NotImplementedError

    def render_key(self, key: str, slug: bool = False, extra: Optional[Dict[str, str]] = None) -> Any:
        value = self.metadata.get(key)
        return self.render(value, slug=slug, extra=extra)

    def render(self, value: Any, slug: bool = False, extra: Optional[Dict[str, str]] = None) -> Any:
        if value in (None, True, False):
            return value
        kwargs = {
            "slug": slug,
            "extra": (extra or {"MENU_ITEM_LOCATION": str(self.location)}),
        }
        if isinstance(value, str):
            return self.menu.render(value, **kwargs)
        if hasattr(value, "items"):
            return {
                key: self.menu.render(value, **kwargs)
                for key, value in value.items()
            }
        return [self.menu.render(item, **kwargs) for item in value]

    def _precreate(self):
        """
        Logic to run before the shortcut files are created.
        """
        if os.name == "nt":
            raise NotImplementedError

        precreate_code = self.render_key("precreate")
        if not precreate_code:
            return
        with NamedTemporaryFile(delete=False, mode="w") as tmp:
            tmp.write(precreate_code)
        if precreate_code.startswith("#!"):
            os.chmod(tmp.name, 0o755)
            cmd = [tmp.name]
        else:
            cmd = ["bash", tmp.name]
        run(cmd, check=True)
        os.unlink(tmp.name)

    def _paths(self) -> Iterable[os.PathLike]:
        """
        This method should return the paths created by the item
        so they can be removed upon uninstallation
        """
        raise NotImplementedError

    @staticmethod
    def _initialize_on_defaults(data) -> Dict:
        with open(data_path("menuinst.menu_item.default.json")) as f:
            defaults = json.load(f)

        return deep_update(defaults, data)

    @staticmethod
    def _flatten_for_platform(data: Mapping, platform: str = sys.platform) -> Mapping:
        """
        Merge platform keys with global keys, overwriting if needed.
        """
        flattened = deepcopy(data)
        all_platforms = flattened.pop("platforms", {})
        this_platform = all_platforms.pop(platform_key(platform), None)
        if this_platform:
            for key, value in this_platform.items():
                if key not in flattened:
                    # bring missing keys, since they are platform specific
                    flattened[key] = value
                elif value is not None:
                    # if the key was in global, it was not platform specific
                    # this is an override and we only do so if is not None
                    log.debug("Platform value %s=%s overrides global value", key, value)
                    flattened[key] = value
        else:  # restore
            flattened["platforms"] = all_platforms

        # in the merged metadata, platforms becomes a list of str stating which
        # platforms are enabled for this item
        flattened["platforms"] = [
            key for key, value in data["platforms"].items() if value is not None
        ]
        return flattened

    def enabled_for_platform(self, platform: str = sys.platform) -> bool:
        return self._data["platforms"].get(platform_key(platform)) is not None


def platform_key(platform: str = sys.platform) -> str:
    if platform == "win32":
        return "win"
    if platform == "darwin":
        return "osx"
    if platform.startswith("linux"):
        return "linux"

    raise ValueError(f"Platform {platform} is not supported")


menuitem_defaults = json.loads(
    (Path(__file__).parents[1] / "data" / "menuinst.menu_item.default.json").read_text()
)
