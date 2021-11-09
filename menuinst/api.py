"""
"""

from os import PathLike
import sys
from typing import Union, List
from pathlib import Path
import warnings

from .platforms import Menu, MenuItem
from .schema import validate


__all__ = [
    "install",
    "remove",
    "install_all",
    "remove_all",
]


def install(
    metadata_or_path: Union[PathLike, dict],
    target_prefix: PathLike = sys.prefix,
    base_prefix: PathLike = sys.prefix,
) -> List[PathLike]:
    metadata = validate(metadata_or_path)
    menu = Menu(metadata.menu_name, target_prefix, base_prefix)

    if not metadata.enabled_for_platform():
        warnings.warning(f"Metadata for {metadata.name} is not enabled for {sys.platform}")
        return

    paths = []
    menu_dirs = menu.create()
    if menu_dirs:
        paths.extend(list(menu_dirs))

    for item in metadata.menu_items:
        menu_item = MenuItem(menu, item)
        menu_item_paths = menu_item.create()
        paths.extend(list(menu_item_paths))

    return paths


def remove(
    metadata_or_path: Union[PathLike, dict],
    target_prefix: PathLike = sys.prefix,
    base_prefix: PathLike = sys.prefix,
) -> List[PathLike]:
    metadata = validate(metadata_or_path)
    menu = Menu(metadata.menu_name, target_prefix, base_prefix)

    if not metadata.enabled_for_platform():
        warnings.warning(f"Metadata for {metadata.name} is not enabled for {sys.platform}")
        return

    for item in metadata.menu_items:
        menu_item = MenuItem(menu, item)
        menu_item.remove()
    menu.remove()


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
