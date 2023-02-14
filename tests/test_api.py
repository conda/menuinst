""""""
import os
import plistlib
import subprocess
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import sleep, time

import pytest
from conftest import DATA, PLATFORM

from menuinst.api import install
from menuinst.utils import DEFAULT_PREFIX


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
    # delete_files += list(paths)

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
        process = subprocess.run([str(executable)], text=True, capture_output=True)
        if process.returncode:
            print(process.stdout, file=sys.stdout)
            print(process.stderr, file=sys.stderr)
            process.check_returncode()
        output = process.stdout
    elif PLATFORM == 'win':
        lnk = next(p for p in paths if p.suffix == ".lnk")
        assert lnk.is_file()
        # os.startfile does not propagate custom env vars,
        # so we need to hardcode it with templating
        # (see block at the beginning of the function)
        os.startfile(lnk)
        # startfile returns immediately; poll for the output file
        # powershell + cmd take a couple seconds to start + activate env
        start = time()
        while not os.path.isfile(win_output_file):
            sleep(1)
            if time() >= start + 10:
                raise RuntimeError(f"Timeout. File '{win_output_file}' was not created!")
        with open(win_output_file) as f:
            output = f.read()

    if expected_output is not None:
        assert output.strip() == expected_output

    return paths, output


def test_install_prefix(delete_files):
    check_output_from_shortcut(delete_files, "sys-prefix.json", expected_output=sys.prefix)


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

    for path in app_dir.rglob("Info.plist"):
        plist = plistlib.loads(path.read_bytes())
        assert plist
        assert "entitlements" not in plist
        break
    else:
        raise AssertionError("Didn't find Info.plist")

    for path in app_dir.rglob("Entitlements.plist"):
        plist = plistlib.loads(path.read_bytes())
        assert plist
        break
    else:
        raise AssertionError("Didn't find Entitlements.plist")


@pytest.mark.skipif(PLATFORM != "osx", reason="macOS only")
def test_no_entitlements_no_signature(delete_files):
    paths, _ = check_output_from_shortcut(delete_files, "sys-prefix.json", expected_output=sys.prefix)
    app_dir = next(p for p in paths if p.name.endswith('.app'))
    launcher = next(p for p in (app_dir / "Contents" / "MacOS").iterdir() if not p.name.endswith('-script'))
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_call(["/usr/bin/codesign", "--verbose", "--verify", str(app_dir)])
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_call(["/usr/bin/codesign", "--verbose", "--verify", str(launcher)])


@pytest.mark.skipif(PLATFORM != "osx", reason="macOS only")
def test_info_plist(delete_files):
    paths, _ = check_output_from_shortcut(
        delete_files,
        "entitlements.json",
        expected_output="entitlements"
    )
    app_dir = next(p for p in paths if p.name.endswith('.app'))

    for path in app_dir.rglob("Info.plist"):
        plist = plistlib.loads(path.read_bytes())
        assert plist
        break
    else:
        raise AssertionError("Didn't find file")

    assert plist["LSEnvironment"]["example_var"] == "example_value"


@pytest.mark.skipif(PLATFORM != "osx", reason="macOS only")
def test_osx_symlinks(delete_files):
    paths, output = check_output_from_shortcut(
        delete_files,
        "osx_symlinks.json",
    )
    app_dir = next(p for p in paths if p.name.endswith('.app'))
    symlinked_python = app_dir / "Contents" / "Resources" / "python"
    assert output.strip() == str(symlinked_python)
    assert symlinked_python.resolve() == (Path(DEFAULT_PREFIX) / "bin" / "python").resolve()
