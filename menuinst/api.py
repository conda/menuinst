""" """

from __future__ import annotations

import json
import os
import sys
import warnings
from logging import getLogger
from pathlib import Path
from typing import Callable, Union

from .platforms import Menu, MenuItem
from .utils import (
    DEFAULT_BASE_PREFIX,
    DEFAULT_PREFIX,
    _UserOrSystem,
    elevate_as_needed,
    read_menuinst_toml,
    user_is_admin,
    write_menuinst_toml,
)

log = getLogger(__name__)


__all__ = [
    "install",
    "remove",
    "install_all",
    "remove_all",
]


def _maybe_try_user(base_prefix: str, target_prefix: str) -> bool:
    if not user_is_admin():
        return False
    if Path(target_prefix, ".nonadmin").is_file():
        return True
    return Path(base_prefix, ".nonadmin").is_file()


def record_shortcuts(
    prefix: Path,
    base_prefix: Path,
    source: str,
    paths: list[os.PathLike],
    distribution_name: str | None = None,
) -> None:
    """Record created shortcuts to menuinst.toml."""
    if not paths:
        return

    data = read_menuinst_toml(prefix)

    # Write distribution_name only to base prefix, and only if not already set
    if prefix.samefile(base_prefix) and distribution_name:
        data.setdefault("distribution_name", distribution_name)

    # Append shortcuts
    shortcuts = data.setdefault("shortcuts", [])
    for path in paths:
        shortcuts.append({"source": source, "path": str(path)})

    write_menuinst_toml(prefix, data)


def remove_shortcut_records(prefix: Path, source: str) -> None:
    """Remove shortcut entries matching source from menuinst.toml.

    TODO: Use the recorded paths as the source of truth for shortcut removal,
    instead of recomputing paths from menu JSON metadata. This would handle
    cases where shortcuts were moved or the menu JSON changed.
    """
    data = read_menuinst_toml(prefix)
    if not data:
        return

    shortcuts = data.get("shortcuts", [])
    if not shortcuts:
        return

    # Filter out entries matching this source
    filtered = [s for s in shortcuts if s.get("source") != source]
    if len(filtered) == len(shortcuts):
        return  # Nothing was removed

    data["shortcuts"] = filtered
    write_menuinst_toml(prefix, data)


def _load(
    metadata_or_path: os.PathLike | dict,
    target_prefix: str | None = None,
    base_prefix: str | None = None,
    _mode: _UserOrSystem = "user",
) -> tuple[Menu, list[MenuItem]]:
    target_prefix = target_prefix or DEFAULT_PREFIX
    base_prefix = base_prefix or DEFAULT_BASE_PREFIX
    if isinstance(metadata_or_path, (str, Path)):
        with open(metadata_or_path) as f:
            metadata = json.load(f)
    else:
        metadata = metadata_or_path
    menu = Menu(metadata["menu_name"], target_prefix, base_prefix, _mode)
    menu_items = [MenuItem(menu, item) for item in metadata["menu_items"]]
    return menu, menu_items


@elevate_as_needed
def install(
    metadata_or_path: Union[os.PathLike, dict],
    *,
    target_prefix: str | None = None,
    base_prefix: str | None = None,
    _mode: _UserOrSystem = "user",
) -> list[os.PathLike]:
    target_prefix = target_prefix or DEFAULT_PREFIX
    base_prefix = base_prefix or DEFAULT_BASE_PREFIX
    menu, menu_items = _load(metadata_or_path, target_prefix, base_prefix, _mode)
    menu_items = [item for item in menu_items if item.enabled_for_platform()]
    if not menu_items:
        warnings.warn(f"Metadata for {menu.name} is not enabled for {sys.platform}")
        return []

    paths = []
    paths += menu.create()
    for menu_item in menu_items:
        paths += menu_item.create()

    # Record shortcuts to menuinst.toml
    if isinstance(metadata_or_path, (str, Path)):
        source = Path(metadata_or_path).name
    else:
        source = f"{menu.name}.json"
    record_shortcuts(
        Path(target_prefix),
        Path(base_prefix),
        source,
        paths,
        distribution_name=menu.placeholders.get("DISTRIBUTION_NAME"),
    )

    return paths


@elevate_as_needed
def remove(
    metadata_or_path: Union[os.PathLike, dict],
    *,
    target_prefix: str | None = None,
    base_prefix: str | None = None,
    _mode: _UserOrSystem = "user",
) -> list[os.PathLike]:
    target_prefix = target_prefix or DEFAULT_PREFIX
    base_prefix = base_prefix or DEFAULT_BASE_PREFIX
    menu, menu_items = _load(metadata_or_path, target_prefix, base_prefix, _mode)
    menu_items = [item for item in menu_items if item.enabled_for_platform()]
    if not menu_items:
        warnings.warn(f"Metadata for {menu.name} is not enabled for {sys.platform}")
        return []

    paths = []
    for menu_item in menu_items:
        paths += menu_item.remove()
    paths += menu.remove()

    if not paths and _maybe_try_user(target_prefix, base_prefix):
        menu, menu_items = _load(metadata_or_path, target_prefix, base_prefix, "user")
        menu_items = [item for item in menu_items if item.enabled_for_platform()]
        for menu_item in menu_items:
            paths += menu_item.remove()
        paths += menu.remove()

    # Remove shortcut records from menuinst.toml
    if isinstance(metadata_or_path, (str, Path)):
        source = Path(metadata_or_path).name
    else:
        source = f"{menu.name}.json"
    remove_shortcut_records(Path(target_prefix), source)

    return paths


@elevate_as_needed
def install_all(
    *,
    target_prefix: str | None = None,
    base_prefix: str | None = None,
    filter: Callable | None = None,
    _mode: _UserOrSystem = "user",
) -> list[tuple[os.PathLike]]:
    target_prefix = target_prefix or DEFAULT_PREFIX
    base_prefix = base_prefix or DEFAULT_BASE_PREFIX
    return _process_all(install, target_prefix, base_prefix, filter, _mode)


@elevate_as_needed
def remove_all(
    *,
    target_prefix: str | None = None,
    base_prefix: str | None = None,
    filter: Callable | None = None,
    _mode: _UserOrSystem = "user",
) -> list[tuple[os.PathLike]]:
    target_prefix = target_prefix or DEFAULT_PREFIX
    base_prefix = base_prefix or DEFAULT_BASE_PREFIX
    return _process_all(remove, target_prefix, base_prefix, filter, _mode)


def _process_all(
    function: Callable[
        [Union[os.PathLike, dict], str | None, str | None, _UserOrSystem], list[os.PathLike]
    ],
    target_prefix: str | None = None,
    base_prefix: str | None = None,
    filter: Callable | None = None,
    _mode: _UserOrSystem = "user",
) -> list[tuple[os.PathLike]]:
    target_prefix = target_prefix or DEFAULT_PREFIX
    base_prefix = base_prefix or DEFAULT_BASE_PREFIX
    jsons = (Path(target_prefix) / "Menu").glob("*.json")
    results = []
    for path in jsons:
        if filter is not None and filter(path):
            try:
                results.append(
                    function(
                        path,
                        target_prefix=target_prefix,
                        base_prefix=base_prefix,
                        _mode=_mode,
                    )
                )
            except json.JSONDecodeError as exc:
                log.warning(f"Skipping {path}: malformed JSON ({exc})")
    return results


_api_remove = remove  # alias to prevent shadowing in the function below


def _install_adapter(path: str, remove: bool = False, prefix: str = DEFAULT_PREFIX, **kwargs):
    """
    This function is only here as a legacy adapter for menuinst v1.x.
    Please use `menuinst.api` functions instead.
    """
    if os.name == "nt":
        path = path.replace("/", "\\")
    json_path = os.path.join(prefix, path)
    with open(json_path) as f:
        metadata = json.load(f)
    if "$schema" not in metadata and "$id" not in metadata:  # old style JSON
        from ._legacy import install as _legacy_install

        if os.name == "nt":
            kwargs.setdefault("root_prefix", kwargs.pop("base_prefix", DEFAULT_BASE_PREFIX))
            if kwargs["root_prefix"] is None:
                kwargs["root_prefix"] = DEFAULT_BASE_PREFIX
            _legacy_install(json_path, remove=remove, prefix=prefix, **kwargs)
        else:
            log.warning(
                "menuinst._legacy is only supported on Windows. "
                "Switch to the new-style menu definitions "
                "for cross-platform compatibility."
            )
    else:
        # patch kwargs to reroute root_prefix to base_prefix
        kwargs.setdefault("base_prefix", kwargs.pop("root_prefix", DEFAULT_BASE_PREFIX))
        if kwargs["base_prefix"] is None:
            kwargs["base_prefix"] = DEFAULT_BASE_PREFIX
        # Pass path so install/remove records the actual filename in menuinst.toml
        if remove:
            _api_remove(json_path, target_prefix=prefix, **kwargs)
        else:
            install(json_path, target_prefix=prefix, **kwargs)
