"""
"""

from os import PathLike
import sys
from typing import Union, List, Tuple
from pathlib import Path
import warnings
import json
from logging import getLogger

from .platforms import Menu, MenuItem

log = getLogger(__name__)


__all__ = [
    "install",
    "remove",
    "install_all",
    "remove_all",
]


def _load(
    metadata_or_path: Union[PathLike, dict],
    target_prefix: PathLike = sys.prefix,
    base_prefix: PathLike = sys.prefix,
) -> Tuple[Menu, List[MenuItem]]:
    if isinstance(metadata_or_path, (str, Path)):
        with open(metadata_or_path) as f:
            metadata = json.load(f)
    else:
        metadata = metadata_or_path

    menu = Menu(metadata["menu_name"], target_prefix, base_prefix)
    menu_items = [MenuItem(menu, item) for item in metadata["menu_items"]]
    return menu, menu_items


def install(
    metadata_or_path: Union[PathLike, dict],
    target_prefix: PathLike = sys.prefix,
    base_prefix: PathLike = sys.prefix,
) -> List[PathLike]:
    menu, menu_items = _load(metadata_or_path, target_prefix, base_prefix)
    if not any(item.enabled_for_platform() for item in menu_items):
        warnings.warning(f"Metadata for {menu.name} is not enabled for {sys.platform}")
        return ()

    paths = []
    paths += menu.create()
    for menu_item in menu_items:
        paths += menu_item.create()

    return paths


def remove(
    metadata_or_path: Union[PathLike, dict],
    target_prefix: PathLike = sys.prefix,
    base_prefix: PathLike = sys.prefix,
) -> List[PathLike]:
    menu, menu_items = _load(metadata_or_path, target_prefix, base_prefix)
    if not any(item.enabled_for_platform() for item in menu_items):
        warnings.warning(f"Metadata for {menu.name} is not enabled for {sys.platform}")
        return ()

    paths = []
    for menu_item in menu_items:
        paths += menu_item.remove()
    paths += menu.remove()

    return paths


def install_all(
    target_prefix: PathLike = sys.prefix,
    base_prefix: PathLike = sys.prefix,
    filter: callable = None,
) -> List[List[PathLike]]:
    return _process_all(target_prefix, base_prefix, filter, action="install")


def remove_all(
    target_prefix: PathLike = sys.prefix,
    base_prefix: PathLike = sys.prefix,
    filter: callable = None,
) -> List[List[Union[str, PathLike]]]:
    return _process_all(target_prefix, base_prefix, filter, action="remove")


def _process_all(target_prefix, base_prefix, filter, action="install"):
    actions = {"install": install, "remove": remove}
    assert action in actions, f"`action` must be one of {tuple(actions.keys())}"
    jsons = (Path(target_prefix) / "Menu").glob("*.json")
    results = []
    for path in jsons:
        if filter is not None and filter(path):
            results.append(actions[action](path, target_prefix, base_prefix))
    return results
