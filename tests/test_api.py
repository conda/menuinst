""""""
import os
import sys
import subprocess
from time import sleep
from tempfile import NamedTemporaryFile

import pytest

from menuinst.api import install
from conftest import DATA, PLATFORM


def check_output_from_shortcut(delete_files, json_path, expected_output=None):
    paths = install(DATA / "jsons" / json_path)
    delete_files += list(paths)

    if PLATFORM == 'linux':
        desktop = next(p for p in paths if p.suffix == ".desktop")
        with open(desktop) as f:
            for line in f:
                if line.startswith("Exec="):
                    cmd = line.split("=", 1)[1].strip()
                    break
            else:
                raise ValueError("Didn't find Exec line")
        output = subprocess.check_output(cmd, shell=True, universal_newlines=True)
    elif PLATFORM == 'osx':
        app_location = paths[0]
        executable = next(p for p in (app_location / "Contents" / "MacOS").iterdir() if not p.name.endswith('-script'))
        output = subprocess.check_output([str(executable)], universal_newlines=True)
    elif PLATFORM == 'win':
        lnk = next(p for p in paths if p.suffix == ".lnk")
        assert lnk.is_file()
        try:
            with NamedTemporaryFile() as tmp:
                os.environ['WIN_OUTPUT_FILE'] = tmp.name
                os.startfile(lnk)
                sleep(1)
                with open(tmp.name) as f:
                    output = f.read()
        finally:
            del os.environ['WIN_OUTPUT_FILE']

    if expected_output is not None:
        assert output.strip() == expected_output
    
    return paths


def test_install_example_1(delete_files):
    check_output_from_shortcut(delete_files, "sys-executable.json", expected_output=sys.executable)


def test_precommands(delete_files):
    check_output_from_shortcut(delete_files, "precommands.json", expected_output="rhododendron and bees")


@pytest.mark.skipif(PLATFORM != "osx", reason="macOS only")
def test_entitlements(delete_files):
    paths = check_output_from_shortcut(delete_files, "entitlements.json", expected_output="entitlements")
    # verify signature
    app_dir = next(p for p in paths if p.name.endswith('.app'))
    subprocess.check_call(["/usr/bin/codesign", "--verbose", "--verify", str(app_dir)])

    launcher = next(p for p in (app_dir / "Contents" / "MacOS").iterdir() if not p.name.endswith('-script'))
    subprocess.check_call(["/usr/bin/codesign", "--verbose", "--verify", str(launcher)])


@pytest.mark.skipif(PLATFORM != "osx", reason="macOS only")
def test_no_entitlements_no_signature(delete_files):
    paths = check_output_from_shortcut(delete_files, "sys-executable.json", expected_output=sys.executable)
    app_dir = next(p for p in paths if p.name.endswith('.app'))
    launcher = next(p for p in (app_dir / "Contents" / "MacOS").iterdir() if not p.name.endswith('-script'))
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_call(["/usr/bin/codesign", "--verbose", "--verify", str(app_dir)])
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_call(["/usr/bin/codesign", "--verbose", "--verify", str(launcher)])
