from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

import pytest
from conda.base.context import context
from conftest import DATA
from menuinst.cli.plugin import conda_subcommands

from menuinst.api import install, remove

if TYPE_CHECKING:
    from pathlib import Path

    from conda.testing.fixtures import CondaCLIFixture, TmpEnvFixture


def test_subcommands_hook() -> None:
    subcommands = list(conda_subcommands())
    assert len(subcommands) == 1
    assert subcommands[0].name == "menuinst"
    assert "menuinst" in context.plugin_manager.get_subcommands()


def test_subcommand_menuinst(conda_cli: CondaCLIFixture) -> None:
    with pytest.raises(SystemExit) as exc:
        stdout, stderr, errorcode = conda_cli("menuinst", "--help")
        assert stdout
        assert not stderr
        assert not errorcode
    assert exc.value.code == 0


@pytest.mark.parametrize("prefix_method", ("prefix", "name", "envvar"))
def test_plugin_install_remove(
    conda_cli: CondaCLIFixture,
    tmp_env: TmpEnvFixture,
    monkeypatch: pytest.MonkeyPatch,
    prefix_method: str,
    delete_files: list[Path],
):
    with tmp_env() as prefix:
        if prefix_method == "prefix":
            prefix_cmd = ["-p", str(prefix)]
        elif prefix_method == "name":
            # The temporary environment becomes the base environment
            prefix_cmd = ["-n", "base"]
        else:
            prefix_cmd = []
            monkeypatch.setenv("CONDA_PREFIX", str(prefix))
        menu_dir = prefix / "Menu"
        menu_dir.mkdir(exist_ok=True, parents=True)
        metadata_file = DATA / "jsons" / "sys-prefix.json"
        dest_path = menu_dir / metadata_file.name
        shutil.copy(metadata_file, dest_path)
        # The plug-in uses the CLIm which calls _install_adapter.
        # That function returns None to be compatible with v1 shortcuts.
        # So, use installing and removing as a workaround to detect expected files.
        paths = set(install(dest_path, target_prefix=prefix, base_prefix=prefix, _mode="user"))
        delete_files.extend(paths)
        files_found = set(filter(lambda x: x.exists(), paths))
        assert files_found == paths
        remove(dest_path, target_prefix=prefix, base_prefix=prefix, _mode="user")
        files_found = set(filter(lambda x: x.exists(), paths))
        assert files_found == set()

        conda_cli("menuinst", "--install", *prefix_cmd, "--root-prefix", str(prefix))
        files_found = set(filter(lambda x: x.exists(), paths))
        assert files_found == paths
        conda_cli("menuinst", "--remove", *prefix_cmd, "--root-prefix", str(prefix))
        files_found = set(filter(lambda x: x.exists(), paths))
        assert files_found == set()


def test_plugin_cli_error(conda_cli: CondaCLIFixture, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    with pytest.raises(ValueError):
        conda_cli("menuinst", "--install")
