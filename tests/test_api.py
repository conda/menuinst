""""""
import os
import sys
import subprocess
from tempfile import NamedTemporaryFile
from time import sleep

import pytest

from menuinst.api import install
from conftest import DATA, PLATFORM


def check_output_from_shortcut(delete_files, json_path, expected_output=None):
    abs_json_path = DATA / "jsons" / json_path
    if PLATFORM == "win":
        with open(abs_json_path) as f:
            contents = f.read()
        with NamedTemporaryFile(suffix=json_path, mode="w",  delete=False) as tmp:
            win_output_file = tmp.name + ".out"
            contents = contents.replace("__WIN_OUTPUT_FILE__", win_output_file.replace("\\", "\\\\"))
            tmp.write(contents)
        abs_json_path = tmp.name
        delete_files.append(abs_json_path)

    paths = install(abs_json_path)
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
        # os.startfile does not propagate custom env vars, 
        # so we need to hardcode it with templating (see block at the beginning of the function)
        os.startfile(lnk)
        sleep(1)
        with open(win_output_file) as f:
            output = f.read()

    if expected_output is not None:
        assert output.strip() == expected_output
    
    return paths, output


def test_install_example_1(delete_files):
    check_output_from_shortcut(delete_files, "sys-executable.json", expected_output=sys.executable)


def test_precommands(delete_files):
    check_output_from_shortcut(delete_files, "precommands.json", expected_output="rhododendron and bees")


@pytest.mark.skipif(PLATFORM != "osx", reason="macOS only")
def test_entitlements(delete_files):
    paths, _ = check_output_from_shortcut(delete_files, "entitlements.json", expected_output="entitlements")
    # verify signature
    app_dir = next(p for p in paths if p.name.endswith('.app'))
    subprocess.check_call(["/usr/bin/codesign", "--verbose", "--verify", str(app_dir)])

    launcher = next(p for p in (app_dir / "Contents" / "MacOS").iterdir() if not p.name.endswith('-script'))
    subprocess.check_call(["/usr/bin/codesign", "--verbose", "--verify", str(launcher)])


@pytest.mark.skipif(PLATFORM != "osx", reason="macOS only")
def test_no_entitlements_no_signature(delete_files):
    paths, _ = check_output_from_shortcut(delete_files, "sys-executable.json", expected_output=sys.executable)
    app_dir = next(p for p in paths if p.name.endswith('.app'))
    launcher = next(p for p in (app_dir / "Contents" / "MacOS").iterdir() if not p.name.endswith('-script'))
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_call(["/usr/bin/codesign", "--verbose", "--verify", str(app_dir)])
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_call(["/usr/bin/codesign", "--verbose", "--verify", str(launcher)])
