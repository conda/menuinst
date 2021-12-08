"""
Integration tests with conda
"""
import os
import sys
from subprocess import check_output, run, PIPE
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


ENV_VARS = {
    k: v for (k, v) in os.environ.copy().items()
    if not k.startswith(("CONDA", "_CONDA", "MAMBA", "_MAMBA"))
}
ENV_VARS["CONDA_VERBOSITY"] = "3"


@contextmanager
def new_environment(*packages):
    prefix = mkdtemp()
    env = ENV_VARS.copy()
    env["CONDA_PKGS_DIRS"] = prefix
    print("--- CREATING", prefix, "---")
    cmd = ["conda", "create", "-y", "--offline", "-p", prefix] + [str(p) for p in packages]
    process = run(
        cmd,
        env=env,
        stdout=PIPE,
        stderr=PIPE,
        universal_newlines=True,
    )
    print(process.stdout)
    print(process.stderr, file=sys.stderr)
    process.check_returncode()

    if "menuinst Exception" in process.stdout:
        raise RuntimeError(
            f"Command {cmd} exited with 0 but "
            f"stdout contained exception:\n{process.stdout}"
        )

    # check_call(["conda", "update", "--all", "-p", prefix])
    yield prefix
    print("--- REMOVING", prefix, "---")
    cmd = ["conda", "remove", "--all", "-y", "-p", prefix]
    process = run(
        cmd,
        env=ENV_VARS,
        stdout=PIPE,
        stderr=PIPE,
        universal_newlines=True,
    )
    print(process.stdout)
    print(process.stderr, file=sys.stderr)
    process.check_returncode()
    shutil.rmtree(prefix, ignore_errors=True)


@contextmanager
def install_package_1():
    """
    This package is shipped with the test data and contains two menu items.

    Both will echo the `CONDA_PREFIX` environment variable. However, the
    first one preactivates the environment, while the second does not. This
    means that the first shortcut will successfully echo the prefix path,
    while the second one will be empty (Windows) or "N/A" (Unix).
    """
    with new_environment(DATA / "pkgs" / "noarch" / "package_1-0.1-0.tar.bz2") as prefix:
        menu_file = Path(prefix) / "Menu" / "package_1.json"
        with open(menu_file) as f:
            meta = json.load(f)
            assert len(meta["menu_items"]) == 2
        assert menu_file.is_file()
        yield prefix, menu_file
    assert not menu_file.is_file()


def test_conda_recent_enough():
    data = json.loads(check_output(["conda", "info", "--json"]))
    assert VersionOrder(data["conda_version"]) >= VersionOrder("4.12a0")


@pytest.mark.skipif(PLATFORM != "linux", reason="Linux only")
def test_package_1_linux():
    with install_package_1() as (prefix, menu_file):
        meta = validate(menu_file)
        menu = Menu(meta.menu_name, str(prefix), BASE_PREFIX)
        items = [menu]

        with open(menu.menu_config_location) as f:
            original_xml = f.read()

        # First case, activation is on, output should be the prefix path
        # Second case, activation is off, output should be N/A
        for item, expected_output in zip(meta.menu_items, (str(prefix), "N/A")):
            item = MenuItem(menu, item)
            items.append(item)
            command = item._command()
            print(command)
            print("-----")
            output = check_output(command, shell=True, universal_newlines=True, env=ENV_VARS)
            assert output.strip() == expected_output

    assert not Path(prefix).exists()
    for item in items:
        for path in item._paths():
            assert not path.exists()

    with open(menu.menu_config_location) as f:
        assert original_xml == f.read()


@pytest.mark.skipif(PLATFORM != "osx", reason="MacOS only")
def test_package_1_osx():
    with install_package_1() as (prefix, menu_file):
        meta = validate(menu_file)
        menu = Menu(meta.menu_name, str(prefix), BASE_PREFIX)
        items = [menu]
        # First case, activation is on, output should be the prefix path
        # Second case, activation is off, output should be N/A
        for item, expected_output in zip(meta.menu_items, (str(prefix), "N/A")):
            item = MenuItem(menu, item)
            items.append(item)
            script = item._write_script(script_path=NamedTemporaryFile(suffix=".sh", delete=False).name)
            print(item._command())
            print("-------------")
            output = check_output(["bash", script], universal_newlines=True, env=ENV_VARS)
            Path(script).unlink()
            assert output.strip() == expected_output

    assert not Path(prefix).exists()
    for item in items:
        for path in item._paths():
            assert not path.exists()


@pytest.mark.skipif(PLATFORM != "win", reason="Windows only")
def test_package_1_windows():
    with install_package_1() as (prefix, menu_file):
        meta = validate(menu_file)
        menu = Menu(meta.menu_name, str(prefix), BASE_PREFIX)
        items = [menu]
        # First case, activation is on, output should be the prefix path
        # Second case, activation is off, output should be empty
        for item, expected_output in zip(meta.menu_items, (str(prefix), "")):
            item = MenuItem(menu, item)
            items.append(item)
            script = item._write_script(script_path=NamedTemporaryFile(suffix=".bat", delete=False).name)
            print(item._command())
            print("-------------")
            output = check_output(["cmd.exe", "/C", f"conda deactivate && conda deactivate && {script}"], universal_newlines=True, env=ENV_VARS)
            Path(script).unlink()
            output = output.replace("ECHO is off.", "")
            assert output.strip() == expected_output

    assert not Path(prefix).exists()
    for item in items:
        for path in item._paths():
            assert not path.exists()
