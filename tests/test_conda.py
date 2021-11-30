"""
Integration tests with conda
"""
import sys
from subprocess import check_call, check_output
from tempfile import TemporaryDirectory
from pathlib import Path
from contextlib import contextmanager
import json

import pytest
from conda.models.version import VersionOrder

from conftest import DATA, PLATFORM


@contextmanager
def new_environment(*packages):
    with TemporaryDirectory() as prefix:
        check_call( ["conda", "create", "-y", "-p", prefix] + [str(p) for p in packages])
        # check_call(["conda", "update", "--all", "-p", prefix])
        yield prefix
        check_call(["conda", "env", "remove", "-y", "-p", prefix])


@contextmanager
def install_package_1():
    with new_environment(DATA / "pkgs" / "noarch" / "package_1-0.1-0.tar.bz2") as prefix:
        menu_file = Path(prefix) / "Menu" / "package_1.json"
        assert menu_file.is_file()
        yield prefix
    assert not menu_file.is_file()


def test_conda_recent_enough():
    data = json.loads(check_output(["conda", "info", "--json"]))
    assert VersionOrder(data["conda_version"]) >= VersionOrder("4.11a0")


@pytest.mark.skipif(PLATFORM != "linux", reason="Linux only")
def test_install_linux():
    with install_package_1() as prefix:
        # check that .desktop files are created
        ...

@pytest.mark.skipif(PLATFORM != "osx", reason="MacOS only")
def test_install_osx():
    with install_package_1() as prefix:
        # check that .app directory is created
        ...

@pytest.mark.skipif(PLATFORM != "win", reason="Windows only")
def test_install_windows():
    with install_package_1() as prefix:
        # check that .lnk files are created
        ...


def test_noarch_works():
    pass


def test_platform_works():
    pass
