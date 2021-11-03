"""
"""

from os import PathLike
import sys
from typing import Union, List
from pathlib import Path

from .platforms import PlatformMenu
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
    root_prefix: PathLike = sys.prefix,
) -> List[PathLike]:
    metadata = validate(metadata_or_path)
    menu = PlatformMenu.from_schema(metadata)
    return menu.install()


def remove(
    metadata_or_path: Union[PathLike, dict],
    target_prefix: PathLike = sys.prefix,
    root_prefix: PathLike = sys.prefix,
) -> List[PathLike]:
    metadata = validate(metadata_or_path)
    menu = PlatformMenu.from_schema(metadata)
    return menu.remove()


def install_all(
    prefix: PathLike,
    root_prefix: PathLike = sys.prefix,
    filter: callable = None,
) -> List[List[PathLike]]:
    return _process_all(prefix, filter, action="install")


def remove_all(
    prefix: Union[str, PathLike],
    root_prefix: PathLike = sys.prefix,
    filter: callable = None,
) -> List[List[Union[str, PathLike]]]:
    return _process_all(prefix, filter, action="remove")


def _process_all(prefix, filter, action="install"):
    actions = {"install": install, "remove": remove}
    assert action in actions, f"`action` must be one of {tuple(actions.keys())}"
    jsons = (Path(prefix) / "Menu").glob("*.json")
    results = []
    for path in jsons:
        if filter is not None and filter(path):
            results.append(actions[action](path))
    return results
