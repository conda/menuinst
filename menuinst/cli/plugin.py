from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from . import _add_install_group, _add_root_prefix, install

try:
    from conda.base.context import locate_prefix_by_name, reset_context
    from conda.cli.helpers import add_parser_prefix
    from conda.plugins.hookspec import hookimpl
    from conda.plugins.types import CondaSubcommand
except ImportError as e:
    raise ImportError("Plugin requires `conda` to be installed.") from e

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace
    from collections.abc import Iterator


def configure_parser(parser: ArgumentParser):
    _add_install_group(parser)
    add_parser_prefix(parser)
    _add_root_prefix(parser)


def execute(args: Namespace):
    root_prefix = args.root_prefix
    if root_prefix:
        root_prefix = str(Path(root_prefix).expanduser().resolve())

    if args.prefix:
        prefix_raw = args.prefix
    elif args.name:
        if root_prefix:
            os.environ["CONDA_ROOT_PREFIX"] = root_prefix
            reset_context()
        prefix_raw = locate_prefix_by_name(args.name)
    elif not (prefix_raw := os.environ.get("CONDA_PREFIX")):
        raise ValueError("No active prefix found and no --prefix or --name given.")
    prefix = Path(prefix_raw).expanduser().resolve()
    install(
        prefix,
        install_shortcuts=args.install,
        remove_shortcuts=args.remove,
        root_prefix=root_prefix,
    )


@hookimpl
def conda_subcommands() -> Iterator[CondaSubcommand]:
    """Return a list of subcommands for the plugin."""
    yield CondaSubcommand(
        name="menuinst",
        action=execute,
        summary="A subcommand for installing and removing shortcuts via menuinst.",
        configure_parser=configure_parser,
    )
