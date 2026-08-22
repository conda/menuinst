"""Unit tests for the ``.desktop`` file written by ``LinuxMenuItem``."""

from __future__ import annotations

import shlex
import subprocess
import sys

import pytest

from menuinst.platforms.linux import LinuxMenu, LinuxMenuItem


@pytest.fixture()
def desktop_entry(tmp_path, monkeypatch):
    """Return a factory that writes a desktop entry and hands back its contents."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))

    def factory(**metadata) -> dict[str, str]:
        menu = LinuxMenu("Test Menu", prefix=sys.prefix, base_prefix=sys.prefix)
        menu._ensure_directories_exist()
        metadata = {"name": "Test Item", "activate": False, **metadata}
        item = LinuxMenuItem(menu, metadata)
        # `MenuItem.__init__` flattens for the platform the tests run on; force
        # Linux so `platforms.linux` keys are picked up off Linux too.
        item.metadata = item._flatten_for_platform(item._data, platform="linux")
        item._write_desktop_file()
        return dict(
            line.split("=", 1) for line in item.location.read_text().splitlines() if "=" in line
        )

    return factory


def test_no_mime_type_has_no_field_code(desktop_entry):
    entry = desktop_entry(command=["echo", "hi"])
    assert not entry["Exec"].endswith(("%f", "%F", "%u", "%U"))


def test_mime_type_adds_file_field_code(desktop_entry):
    entry = desktop_entry(
        command=["echo", "hi"],
        platforms={"linux": {"MimeType": ["application/x-menuinst"]}},
    )
    assert entry["Exec"].endswith('"$@"\' bash %f')


def test_url_scheme_handler_adds_url_field_code(desktop_entry):
    entry = desktop_entry(
        command=["echo", "hi"],
        platforms={"linux": {"MimeType": ["x-scheme-handler/menuinst"]}},
    )
    assert entry["Exec"].endswith('"$@"\' bash %u')


def test_mixed_mime_types_add_file_field_code(desktop_entry):
    entry = desktop_entry(
        command=["echo", "hi"],
        platforms={"linux": {"MimeType": ["x-scheme-handler/menuinst", "application/x-menuinst"]}},
    )
    assert entry["Exec"].endswith('"$@"\' bash %f')


def test_existing_field_code_is_not_duplicated(desktop_entry):
    entry = desktop_entry(
        command=["echo", "%f"],
        platforms={"linux": {"MimeType": ["application/x-menuinst"]}},
    )
    assert entry["Exec"].count("%f") == 1
    assert '"$@"' not in entry["Exec"]


@pytest.mark.skipif(sys.platform == "win32", reason="Requires a POSIX shell")
def test_field_code_argument_reaches_the_command(desktop_entry, tmp_path):
    """The launcher's argument must survive `bash -c` and land in the command."""
    written = tmp_path / "written.txt"
    entry = desktop_entry(
        command=[
            sys.executable,
            "-c",
            f"import pathlib, sys; pathlib.Path({str(written)!r}).write_text(sys.argv[1])",
        ],
        platforms={"linux": {"MimeType": ["application/x-menuinst"]}},
    )
    opened = tmp_path / "opened.menuinst"
    opened.touch()
    # Stand in for the file manager, which substitutes the field code before
    # splitting `Exec` into arguments.
    subprocess.run(shlex.split(entry["Exec"].replace("%f", str(opened))), check=True)
    assert written.read_text() == str(opened)
