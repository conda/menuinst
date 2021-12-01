"""
"""
import os
import sys
import warnings
from typing import Union, List
from pathlib import Path
from subprocess import check_output

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from ..schema import MenuInstSchema
from ..utils import slugify


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

    @property
    def conda_exe(self):
        candidates = (
                self.base_prefix / "_conda.exe",
                Path(os.environ.get("CONDA_EXE", "/oops/a_file_that_does_not_exist")),
                self.base_prefix / "condabin" / "conda",
                self.base_prefix / "bin" / "conda",
                Path(os.environ.get("MAMBA_EXE", "/oops/a_file_that_does_not_exist")),
                self.base_prefix / "condabin" / "micromamba",
                self.base_prefix / "bin" / "micromamba",
        )
        return next((path for path in candidates if path.is_file()), Path("conda"))

    def _is_micromamba(self, exe):
        if "micromamba" in exe.name:
            return True
        if exe.name == "_conda.exe":
            out = check_output([str(exe), "info"], universal_newlines=True)
            return "micromamba version" in out
        return False

class MenuItem:
    def __init__(self, menu: Menu, metadata: MenuInstSchema.MenuItem):
        self.menu = menu
        self.full_metadata = metadata

        if not metadata.enabled_for_platform():
            warnings.warning(f"Metadata for {metadata.name} is not enabled for {sys.platform}")

        self.metadata = metadata.merge_for_platform()

    def create(self) -> List[Path]:
        raise NotImplementedError

    def remove(self) -> List[Path]:
        raise NotImplementedError

    def render(self, key: str, slug=False):
        value = getattr(self.metadata, key)
        if value in (None, True, False):
            return value
        if isinstance(value, str):
            return self.menu.render(value, slug=slug)
        return [self.menu.render(item, slug=slug) for item in value]


def _site_packages_in_unix(prefix):
    """
    Locate the python site-packages location on unix systems
    """
    lib = Path(prefix) / "lib"
    lib_python = next((p for p in lib.glob("python*") if p.is_dir()), lib / "pythonN.A")
    return lib_python / "site-packages"
