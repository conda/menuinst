from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import DATA

from menuinst.api import install, remove
from menuinst.cli import main as menuinst_main


def _setup_menu_directory(prefix: Path) -> dict[str, set[Path]]:
    packages = {
        "sys-prefix": "sys-prefix.json",
        "menu": "sys-prefix-menu_menu.json",
        "suffix": "sys-prefix_suffix.json",
    }
    source = DATA / "jsons" / "sys-prefix.json"
    metadata = json.loads(source.read_text())
    menu_dir = prefix / "Menu"
    menu_dir.mkdir(exist_ok=True, parents=True)
    menu_files = {}
    for package, dest in packages.items():
        metadata_package = metadata.copy()
        metadata_package["menu_items"][0]["name"] += f"_{package}"
        dest_path = menu_dir / dest
        dest_path.write_text(json.dumps(metadata_package))
        # The CLI uses _install_adapter (which returns None) to be compatible with v1 shortcuts.
        # So, use installing and removing as a workaround to detect expected files.
        paths = set(install(dest_path, target_prefix=prefix, base_prefix=prefix, _mode="user"))
        menu_files[package] = paths
        files_found = set(filter(lambda x: x.exists(), paths))
        assert files_found == paths
        remove(dest_path, target_prefix=prefix, base_prefix=prefix, _mode="user")
        files_found = set(filter(lambda x: x.exists(), paths))
        assert files_found == set()
    return menu_files


def test_cli_packages(tmp_path: Path, delete_files: list[Path], run_as_user: None):
    (tmp_path / ".nonadmin").touch()
    menu_files = _setup_menu_directory(tmp_path)
    for files in menu_files.values():
        delete_files.extend(files)
    # The delete_files fixture contains all expected files
    expected_files = set(delete_files)

    menuinst_main(
        ["--install", "sys-prefix", "--prefix", str(tmp_path), "--root-prefix", str(tmp_path)]
    )
    files_found = set(filter(lambda x: x.exists(), expected_files))
    assert files_found == menu_files["sys-prefix"]
    menuinst_main(
        [
            "--install",
            "sys-prefix-menu",
            "sys-prefix_suffix.json",
            "--prefix",
            str(tmp_path),
            "--root-prefix",
            str(tmp_path),
        ]
    )
    files_found = set(filter(lambda x: x.exists(), expected_files))
    assert files_found == expected_files
    menuinst_main(
        [
            "--remove",
            "sys-prefix-menu",
            "sys-prefix_suffix.json",
            "--prefix",
            str(tmp_path),
            "--root-prefix",
            str(tmp_path),
        ]
    )
    files_found = set(filter(lambda x: x.exists(), expected_files))
    assert files_found == menu_files["sys-prefix"]
    menuinst_main(
        ["--remove", "sys-prefix", "--prefix", str(tmp_path), "--root-prefix", str(tmp_path)]
    )
    files_found = set(filter(lambda x: x.exists(), expected_files))
    assert files_found == set()


def test_cli_all(tmp_path: Path, delete_files: list[Path], run_as_user: None) -> None:
    (tmp_path / ".nonadmin").touch()
    menu_files = _setup_menu_directory(tmp_path)
    for files in menu_files.values():
        delete_files.extend(files)
    # The delete_files fixture contains all expected files
    expected_files = set(delete_files)

    menuinst_main(["--install", "--prefix", str(tmp_path), "--root-prefix", str(tmp_path)])
    files_found = set(filter(lambda x: x.exists(), expected_files))
    assert files_found == expected_files
    menuinst_main(["--remove", "--prefix", str(tmp_path), "--root-prefix", str(tmp_path)])
    files_found = set(filter(lambda x: x.exists(), expected_files))
    assert files_found == set()


@pytest.mark.parametrize(
    "argv",
    (
        pytest.param(["--install"], id="prefix missing"),
        pytest.param(["--prefix", "/tmp/somewhere"], id="install/remove missing"),
    ),
)
def test_cli_errors(argv: list[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        menuinst_main(argv)
    assert exc.value.code == 2


@pytest.mark.parametrize(
    "env_var_set,expect_toml",
    [
        pytest.param(True, True, id="env_var_set_creates_toml"),
        pytest.param(False, False, id="no_env_var_no_toml"),
    ],
)
def test_cli_env_var_persistence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, env_var_set: bool, expect_toml: bool
) -> None:
    """Test that MENUINST_DISTRIBUTION_NAME env var is persisted to menuinst.toml."""
    (tmp_path / ".nonadmin").touch()
    (tmp_path / "Menu").mkdir()

    if env_var_set:
        monkeypatch.setenv("MENUINST_DISTRIBUTION_NAME", "TestApp")
    else:
        monkeypatch.delenv("MENUINST_DISTRIBUTION_NAME", raising=False)

    menuinst_main(["--install", "--prefix", str(tmp_path), "--root-prefix", str(tmp_path)])

    toml_path = tmp_path / "Menu" / "menuinst.toml"
    if expect_toml:
        assert toml_path.exists(), "menuinst.toml should be created when env var is set"
        content = toml_path.read_text()
        assert 'distribution_name = "TestApp"' in content
    else:
        assert not toml_path.exists(), "menuinst.toml should not be created without env var"
