"""
"""
import os
import sys
import warnings
from typing import Union, List
from pathlib import Path

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
        self.prefix = prefix
        self.base_prefix = base_prefix

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
            "BASE_PREFIX": self.base_prefix,
            "DISTRIBUTION_NAME": os.path.basename(self.base_prefix),
            "BASE_PYTHON": os.path.join(self.base_prefix, "bin", "python"),
            "PREFIX": self.prefix,
            "ENV_NAME": os.path.basename(self.prefix),
            "PYTHON": os.path.join(self.prefix, "bin", "python"),
            "MENU_DIR": os.path.join(self.prefix, "Menu"),
            "BIN_DIR": os.path.join(self.prefix, "bin"),
            "PY_VER": "",
            "HOME": os.path.expanduser("~"),
            "ICON_EXT": "png",
        }


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
        if value is None:
            return
        if isinstance(value, str):
            return self.menu.render(value, slug=slug)
        return [self.menu.render(item, slug=slug) for item in value]


def _site_packages_in_unix(prefix):
    """
    Locate the python site-packages location on unix systems
    """
    for python_lib in (Path(prefix) / "lib").glob("python*"):
        if python_lib.is_directory():
            break
    else:
        python_lib = prefix / "lib" / "pythonN.A"

    return python_lib / "site-packages"
