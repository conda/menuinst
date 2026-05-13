"""Tests for distribution_name resolution and menuinst.toml tracking."""

import json

import pytest

from menuinst.api import (
    _install_adapter,
    record_shortcuts,
    remove_shortcut_records,
    write_menuinst_toml,
)
from menuinst.platforms import Menu
from menuinst.utils import read_menuinst_toml

# Placeholder distribution names for tests
DIST_NAME = "Something"
DIST_NAME_ALT = "SomethingElse"


class TestGetDistributionName:
    """Tests for Menu._get_distribution_name() resolution order."""

    def test_env_var_takes_priority(self, tmp_path, monkeypatch):
        """MENUINST_DISTRIBUTION_NAME env var should be used when set."""
        monkeypatch.setenv("MENUINST_DISTRIBUTION_NAME", DIST_NAME)
        menu = Menu("test", prefix=str(tmp_path), base_prefix=str(tmp_path))
        assert menu._get_distribution_name() == DIST_NAME
        assert menu.placeholders["DISTRIBUTION_NAME"] == DIST_NAME

    def test_toml_used_when_no_env_var(self, tmp_path, monkeypatch):
        """TOML value should be used when env var is not set."""
        monkeypatch.delenv("MENUINST_DISTRIBUTION_NAME", raising=False)
        write_menuinst_toml(tmp_path, {"distribution_name": DIST_NAME})
        menu = Menu("test", prefix=str(tmp_path), base_prefix=str(tmp_path))
        assert menu._get_distribution_name() == DIST_NAME

    def test_fallback_to_base_prefix_name(self, tmp_path, monkeypatch):
        """Should fall back to base_prefix.name when no env var or TOML."""
        monkeypatch.delenv("MENUINST_DISTRIBUTION_NAME", raising=False)
        menu = Menu("test", prefix=str(tmp_path), base_prefix=str(tmp_path))
        assert menu._get_distribution_name() == tmp_path.name

    def test_env_var_overrides_toml(self, tmp_path, monkeypatch):
        """Env var should take priority over TOML value."""
        monkeypatch.setenv("MENUINST_DISTRIBUTION_NAME", DIST_NAME)
        write_menuinst_toml(tmp_path, {"distribution_name": DIST_NAME_ALT})
        menu = Menu("test", prefix=str(tmp_path), base_prefix=str(tmp_path))
        assert menu._get_distribution_name() == DIST_NAME

    def test_malformed_toml_raises(self, tmp_path, monkeypatch):
        """Malformed TOML should raise an exception."""
        monkeypatch.delenv("MENUINST_DISTRIBUTION_NAME", raising=False)
        toml_path = tmp_path / "Menu" / "menuinst.toml"
        toml_path.parent.mkdir(parents=True, exist_ok=True)
        toml_path.write_text("this is not valid toml {{{{")
        with pytest.raises(ValueError, match="Failed to read"):
            # On Linux, Menu() triggers _get_distribution_name() during __init__,
            # but on Windows/macOS it's lazy. Call it explicitly to ensure the
            # error is raised on all platforms.
            menu = Menu("test", prefix=str(tmp_path), base_prefix=str(tmp_path))
            menu._get_distribution_name()


class TestShortcutRecording:
    """Tests for shortcut recording and removal in menuinst.toml."""

    def test_install_records_to_toml(self, tmp_path, monkeypatch):
        """install() should record shortcuts to menuinst.toml."""
        monkeypatch.delenv("MENUINST_DISTRIBUTION_NAME", raising=False)
        base_prefix = tmp_path / "base"
        base_prefix.mkdir()

        # Test via record_shortcuts directly
        record_shortcuts(
            base_prefix,
            base_prefix,
            "foo.json",
            [tmp_path / "foo.lnk", tmp_path / "bar.lnk"],
            distribution_name=DIST_NAME,
        )

        data = read_menuinst_toml(base_prefix)
        assert data["distribution_name"] == DIST_NAME
        assert len(data["shortcuts"]) == 2
        assert data["shortcuts"][0]["source"] == "foo.json"

    def test_remove_cleans_toml(self, tmp_path, monkeypatch):
        """remove() should clean up TOML entries."""
        monkeypatch.delenv("MENUINST_DISTRIBUTION_NAME", raising=False)
        base_prefix = tmp_path / "base"
        base_prefix.mkdir()

        # Pre-populate TOML with shortcuts from two sources
        write_menuinst_toml(
            base_prefix,
            {
                "distribution_name": DIST_NAME,
                "shortcuts": [
                    {"source": "foo.json", "path": "/path/to/foo.lnk"},
                    {"source": "foo.json", "path": "/path/to/bar.lnk"},
                    {"source": "baz.json", "path": "/path/to/baz.lnk"},
                ],
            },
        )

        # Remove records for foo.json
        remove_shortcut_records(base_prefix, "foo.json")

        data = read_menuinst_toml(base_prefix)
        assert len(data["shortcuts"]) == 1
        assert data["shortcuts"][0]["source"] == "baz.json"
        # distribution_name should be preserved
        assert data["distribution_name"] == DIST_NAME

    def test_distribution_name_only_written_to_base_prefix(self, tmp_path):
        """distribution_name should only be written when prefix == base_prefix."""
        base_prefix = tmp_path / "base"
        env_prefix = tmp_path / "envs" / "foo"
        base_prefix.mkdir(parents=True)
        env_prefix.mkdir(parents=True)

        # Record to base prefix - should include distribution_name
        record_shortcuts(
            base_prefix,
            base_prefix,
            "foo.json",
            [tmp_path / "foo.lnk"],
            distribution_name=DIST_NAME,
        )
        data = read_menuinst_toml(base_prefix)
        assert data.get("distribution_name") == DIST_NAME

        # Record to non-base prefix - should NOT include distribution_name
        record_shortcuts(
            env_prefix,
            base_prefix,
            "bar.json",
            [tmp_path / "bar.lnk"],
            distribution_name=DIST_NAME,
        )
        data = read_menuinst_toml(env_prefix)
        assert "distribution_name" not in data
        assert len(data["shortcuts"]) == 1


class TestInstallAdapter:
    """Tests for _install_adapter recording correct source filename."""

    def test_records_actual_filename_not_menu_name(self, tmp_path, monkeypatch):
        """_install_adapter should record JSON filename, not rendered menu_name."""
        monkeypatch.delenv("MENUINST_DISTRIBUTION_NAME", raising=False)
        (tmp_path / ".nonadmin").touch()
        menu_dir = tmp_path / "Menu"
        menu_dir.mkdir()

        # Create JSON with menu_name containing placeholder
        json_file = menu_dir / "test_shortcut.json"
        json_file.write_text(
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft-07/schema",
                    "menu_name": "{{ DISTRIBUTION_NAME }} Foo Bar",
                    "menu_items": [
                        {
                            "name": "Foo Bar",
                            "command": ["echo", "test"],
                            "activate": False,
                            "platforms": {"linux": {}, "win": {}, "osx": {}},
                        }
                    ],
                }
            )
        )

        _install_adapter(str(json_file), prefix=str(tmp_path), root_prefix=str(tmp_path))

        data = read_menuinst_toml(tmp_path)
        # Source should be the filename, not "{{ DISTRIBUTION_NAME }} Foo Bar.json"
        assert data["shortcuts"][0]["source"] == "test_shortcut.json"
