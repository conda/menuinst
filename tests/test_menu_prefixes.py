"""Tests for how menuinst decides whether a prefix is the base environment."""

from __future__ import annotations

import pytest

from menuinst.platforms.base import Menu, MenuItem

NAME = {
    "target_environment_is_base": "MyApp",
    "target_environment_is_not_base": "MyApp ({{ ENV_NAME }})",
}


def item_name(menu: Menu) -> str:
    return MenuItem(menu, {"name": dict(NAME)}).metadata["name"]


@pytest.fixture()
def root(tmp_path):
    """An installation root holding one named environment, `<root>/envs/myenv`."""
    (tmp_path / "conda-meta").mkdir()
    (tmp_path / "envs" / "myenv" / "conda-meta").mkdir(parents=True)
    return tmp_path


def test_base_prefix_is_base(root):
    menu = Menu("MyApp", prefix=root, base_prefix=root)
    assert menu.is_base_environment
    assert menu.env_name == "base"
    assert item_name(menu) == "MyApp"


def test_named_environment_is_not_base(root):
    menu = Menu("MyApp", prefix=root / "envs" / "myenv", base_prefix=root)
    assert not menu.is_base_environment
    assert menu.env_name == "myenv"
    assert item_name(menu) == "MyApp ({{ ENV_NAME }})"


def test_environment_claiming_to_be_its_own_base_is_not_base(root):
    """A conda installed into an environment reports that environment as its own base."""
    env = root / "envs" / "myenv"
    menu = Menu("MyApp", prefix=env, base_prefix=env)
    assert not menu.is_base_environment
    assert menu.env_name == "myenv"
    assert item_name(menu) == "MyApp ({{ ENV_NAME }})"


def test_base_prefix_outside_an_envs_directory_is_still_base(tmp_path):
    """The `envs` layout is the only thing that overrides `base_prefix`."""
    prefix = tmp_path / "opt" / "myinstall"
    (prefix / "conda-meta").mkdir(parents=True)
    menu = Menu("MyApp", prefix=prefix, base_prefix=prefix)
    assert menu.is_base_environment
    assert menu.env_name == "base"
    assert item_name(menu) == "MyApp"


def test_envs_directory_without_a_conda_root_above_it_is_not_special(tmp_path):
    """
    An installation is only a named environment if the directory above `envs`
    is itself a conda prefix. Without that, `base_prefix` decides as before.
    """
    prefix = tmp_path / "opt" / "envs" / "mydist"
    (prefix / "conda-meta").mkdir(parents=True)
    assert not (tmp_path / "opt" / "conda-meta").exists()
    menu = Menu("MyApp", prefix=prefix, base_prefix=prefix)
    assert menu.is_base_environment
    assert menu.env_name == "base"


def test_missing_prefixes_do_not_raise(tmp_path):
    """`Path.samefile` needs both paths to exist; a torn-down prefix must not crash."""
    gone = tmp_path / "gone"
    assert not gone.exists()
    assert Menu("MyApp", prefix=gone, base_prefix=gone).is_base_environment
    assert not Menu("MyApp", prefix=gone, base_prefix=tmp_path / "other").is_base_environment
