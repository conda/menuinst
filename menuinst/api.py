"""
"""

from os import PathLike
import sys
from typing import Union, List, Tuple, Literal
from pathlib import Path
import warnings
import json
from logging import getLogger

from .platforms import Menu, MenuItem
from .utils import elevate_as_needed, DEFAULT_PREFIX, DEFAULT_BASE_PREFIX

log = getLogger(__name__)


__all__ = [
    "install",
    "remove",
    "install_all",
    "remove_all",
]


def _load(
    metadata_or_path: Union[PathLike, dict],
    target_prefix: PathLike = DEFAULT_PREFIX,
    base_prefix: PathLike = DEFAULT_BASE_PREFIX,
    _mode: Union[Literal["user"], Literal["system"]] = "user",
) -> Tuple[Menu, List[MenuItem]]:
    if isinstance(metadata_or_path, (str, Path)):
        with open(metadata_or_path) as f:
            metadata = json.load(f)
    else:
        metadata = metadata_or_path
    menu = Menu(metadata["menu_name"], target_prefix, base_prefix, _mode)
    menu_items = [MenuItem(menu, item) for item in metadata["menu_items"]]
    return menu, menu_items


# @elevate_as_needed
def install(
    metadata_or_path: Union[PathLike, dict],
    *,
    target_prefix: PathLike = DEFAULT_PREFIX,
    base_prefix: PathLike = DEFAULT_BASE_PREFIX,
    _mode: Union[Literal["user"], Literal["system"]] = "user",
) -> List[PathLike]:
    menu, menu_items = _load(metadata_or_path, target_prefix, base_prefix, _mode)
    if not any(item.enabled_for_platform() for item in menu_items):
        warnings.warn(f"Metadata for {menu.name} is not enabled for {sys.platform}")
        return ()

    paths = []
    paths += menu.create()
    for menu_item in menu_items:
        paths += menu_item.create()

    return paths


# @elevate_as_needed
def remove(
    metadata_or_path: Union[PathLike, dict],
    *,
    target_prefix: PathLike = DEFAULT_PREFIX,
    base_prefix: PathLike = DEFAULT_BASE_PREFIX,
    _mode: Union[Literal["user"], Literal["system"]] = "user",
) -> List[PathLike]:
    menu, menu_items = _load(metadata_or_path, target_prefix, base_prefix, _mode)
    if not any(item.enabled_for_platform() for item in menu_items):
        warnings.warn(f"Metadata for {menu.name} is not enabled for {sys.platform}")
        return ()

    paths = []
    for menu_item in menu_items:
        paths += menu_item.remove()
    paths += menu.remove()

    return paths


# @elevate_as_needed
def install_all(
    *,
    target_prefix: PathLike = DEFAULT_PREFIX,
    base_prefix: PathLike = DEFAULT_BASE_PREFIX,
    filter: Union[callable, None] = None,
    _mode: Union[Literal["user"], Literal["system"]] = "user",
) -> List[List[PathLike]]:
    return _process_all(install, target_prefix, base_prefix, filter, _mode)


# @elevate_as_needed
def remove_all(
    *,
    target_prefix: PathLike = DEFAULT_PREFIX,
    base_prefix: PathLike = DEFAULT_BASE_PREFIX,
    filter: Union[callable, None] = None,
    _mode: Union[Literal["user"], Literal["system"]] = "user",
) -> List[List[Union[str, PathLike]]]:
    return _process_all(remove, target_prefix, base_prefix, filter, _mode)


def _process_all(
    function: callable,
    target_prefix: PathLike = DEFAULT_PREFIX,
    base_prefix: PathLike = DEFAULT_BASE_PREFIX,
    filter: Union[callable, None] = None,
    _mode: Union[Literal["user"], Literal["system"]] = "user",
):
    jsons = (Path(target_prefix) / "Menu").glob("*.json")
    results = []
    for path in jsons:
        if filter is not None and filter(path):
            results.append(function(path, target_prefix, base_prefix, _mode))
    return results
