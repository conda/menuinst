from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from ..api import _install_adapter

_MENU_RE = re.compile(r"(?:[-\._]menu)?\.json$", re.IGNORECASE)


def _add_install_group(parser: argparse.ArgumentParser) -> None:
    install_group = parser.add_mutually_exclusive_group(required=True)
    install_group.add_argument(
        "--install",
        nargs="*",
        metavar="PKG",
        help="create menu items for the given packages; "
        "if none are given, create menu items for all packages "
        "in the prefix",
    )
    install_group.add_argument(
        "--remove",
        nargs="*",
        metavar="PKG",
        help="remove menu items for the given packages; "
        "if none are given, remove menu items for all packages "
        "in the prefix",
    )


def _add_prefix(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--prefix",
        required=True,
        help="The prefix containing the shortcuts metadate inside `Menu`",
    )


def _add_root_prefix(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--root-prefix",
        help="The menuinst base/root prefix",
    )


def configure_parser(parser: argparse.ArgumentParser) -> None:
    _add_prefix(parser)
    _add_install_group(parser)
    _add_root_prefix(parser)


def install(
    prefix: Path,
    root_prefix: str | None = None,
    install_shortcuts: list[str] | None = None,
    remove_shortcuts: list[str] | None = None,
):
    packages = None
    if install_shortcuts is not None:
        packages = install_shortcuts
        remove = False
    elif remove_shortcuts is not None:
        packages = remove_shortcuts
        remove = True
    else:
        raise argparse.ArgumentError(None, "Must select shortcuts to install or remove.")

    if root_prefix:
        root_prefix = str(Path(root_prefix).expanduser().resolve())

    for json_path in (prefix / "Menu").glob("*.json"):
        if (
            packages
            and json_path.name not in packages
            and _MENU_RE.sub("", json_path.name) not in packages
        ):
            continue
        _install_adapter(
            str(json_path), remove=remove, prefix=str(prefix), root_prefix=root_prefix
        )


def main(argv: list[str] = sys.argv[1:]):
    parser = argparse.ArgumentParser()
    configure_parser(parser)
    args = parser.parse_args(argv)
    install(
        Path(args.prefix).expanduser().resolve(),
        root_prefix=args.root_prefix,
        install_shortcuts=args.install,
        remove_shortcuts=args.remove,
    )


if __name__ == "__main__":
    main()
