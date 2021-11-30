"""
Integration tests with conda
"""
import os
from subprocess import check_call, check_output
from tempfile import NamedTemporaryFile, mkdtemp
from pathlib import Path
from contextlib import contextmanager
import json
import shutil

import pytest
from conda.models.version import VersionOrder

from menuinst.platforms import Menu, MenuItem
from menuinst.schema import validate

from conftest import DATA, PLATFORM, BASE_PREFIX


@contextmanager
def new_environment(*packages):
    prefix = mkdtemp()
    check_call( ["conda", "create", "-y", "-p", prefix] + [str(p) for p in packages])
    # check_call(["conda", "update", "--all", "-p", prefix])
    yield prefix
    check_call(["conda", "env", "remove", "-y", "-p", prefix])
    shutil.rmtree(prefix, ignore_errors=True)


@contextmanager
def install_package_1():
    with new_environment(DATA / "pkgs" / "noarch" / "package_1-0.1-0.tar.bz2") as prefix:
        menu_file = Path(prefix) / "Menu" / "package_1.json"
        assert menu_file.is_file()
        yield prefix, menu_file
    assert not menu_file.is_file()


def test_conda_recent_enough():
    data = json.loads(check_output(["conda", "info", "--json"]))
    assert VersionOrder(data["conda_version"]) >= VersionOrder("4.11a0")


@pytest.mark.skipif(PLATFORM != "linux", reason="Linux only")
def test_install_linux():
    with install_package_1() as (prefix, menu_file):
        meta = validate(menu_file)
        menu = Menu(meta.menu_name, str(prefix), BASE_PREFIX)
        item = MenuItem(menu, meta.menu_items[0])
        command = item._command()
        output = check_output(command, shell=True, universal_newlines=True)
        assert output.strip() == str(prefix)

@pytest.mark.skipif(PLATFORM != "osx", reason="MacOS only")
def test_install_osx():
    with install_package_1() as (prefix, menu_file):
        meta = validate(menu_file)
        menu = Menu(meta.menu_name, str(prefix), BASE_PREFIX)
        item = MenuItem(menu, meta.menu_items[0])
        script = item._write_script(script_path=NamedTemporaryFile(suffix=".sh", delete=False).name)
        output = check_output(["bash", script], universal_newlines=True)
        Path(script).unlink()
        assert output.strip() == str(prefix)

@pytest.mark.skipif(PLATFORM != "win", reason="Windows only")
def test_install_windows():
    with install_package_1() as (prefix, menu_file):
        meta = validate(menu_file)
        menu = Menu(meta.menu_name, str(prefix), BASE_PREFIX)
        item = MenuItem(menu, meta.menu_items[0])
        script = item._write_script(script_path=NamedTemporaryFile(suffix=".bat", delete=False).name)
        print(item._command())
        output = check_output(script, shell=True, universal_newlines=True)
        Path(script).unlink()
        assert output.strip() == str(prefix)


def test_noarch_works():
    pass


def test_platform_works():
    pass
