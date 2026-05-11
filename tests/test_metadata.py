"""Tests for distribution_name resolution and menuinst.toml tracking."""

from menuinst.api import (
    read_menuinst_toml,
    record_shortcuts,
    remove_shortcut_records,
    write_menuinst_toml,
)
from menuinst.platforms import Menu

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

    def test_malformed_toml_graceful_fallback(self, tmp_path, monkeypatch, caplog):
        """Malformed TOML should log warning and fall back to base_prefix.name."""
        monkeypatch.delenv("MENUINST_DISTRIBUTION_NAME", raising=False)
        toml_path = tmp_path / "Menu" / "menuinst.toml"
        toml_path.parent.mkdir(parents=True, exist_ok=True)
        toml_path.write_text("this is not valid toml {{{{")
        menu = Menu("test", prefix=str(tmp_path), base_prefix=str(tmp_path))
        assert menu._get_distribution_name() == tmp_path.name
        assert "Failed to read menuinst.toml" in caplog.text


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
