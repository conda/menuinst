""""""
import os
import plistlib
import sys
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import sleep, time

import pytest

from menuinst.api import install
from menuinst.utils import DEFAULT_PREFIX

from conftest import DATA, PLATFORM


def check_output_from_shortcut(
    delete_files,
    json_path,
    expected_output=None,
    action="run_shortcut",
    file_to_open=None,
    url_to_open=None,
):
    assert action in ("run_shortcut", "open_file", "open_url")

    abs_json_path = DATA / "jsons" / json_path
    contents = abs_json_path.read_text()
    if "__OUTPUT_FILE__" in contents:
        with NamedTemporaryFile(suffix=json_path, mode="w", delete=False) as tmp:
            output_file = tmp.name + ".out"
            contents = contents.replace("__OUTPUT_FILE__", output_file.replace("\\", "\\\\"))
            tmp.write(contents)
        abs_json_path = tmp.name
        delete_files.append(abs_json_path)

    paths = install(abs_json_path)
    print(paths)
    # delete_files += list(paths)

    if action == "run_shortcut":
        if PLATFORM == "win":
            lnk = next(p for p in paths if p.suffix == ".lnk")
            assert lnk.is_file()
            os.startfile(lnk)
            t0 = time()
            while not os.path.isfile(output_file):
                sleep(1)
                if time() >= t0 + 10:
                    raise RuntimeError(f"Timeout. File '{output_file}' was not created!")
            with open(output_file) as f:
                output = f.read()
        else:
            if PLATFORM == "linux":
                desktop = next(p for p in paths if p.suffix == ".desktop")
                with open(desktop) as f:
                    for line in f:
                        if line.startswith("Exec="):
                            executable = line.split("=", 1)[1].strip()
                            break
                    else:
                        raise ValueError("Didn't find Exec line")
            elif PLATFORM == "osx":
                app_location = paths[0]
                executable = next(
                    p
                    for p in (app_location / "Contents" / "MacOS").iterdir()
                    if not p.name.endswith("-script")
                )
            process = subprocess.run([str(executable)], text=True, capture_output=True)
            if process.returncode:
                print(process.stdout, file=sys.stdout)
                print(process.stderr, file=sys.stderr)
                process.check_returncode()
            output = process.stdout
    else:
        if action == "open_file":
            assert file_to_open is not None
            with NamedTemporaryFile(suffix=file_to_open, delete=False) as f:
                f.write(b"")
            delete_files.append(f.name)
            arg = f.name
        elif action == "open_url":
            assert url_to_open is not None
            arg = url_to_open
        cmd = {"linux": "xdg-open", "osx": "open", "win": "start"}[PLATFORM]
        process = subprocess.run([cmd, arg], text=True, capture_output=True)
        if process.returncode:
            print(process.stdout, file=sys.stdout)
            print(process.stderr, file=sys.stderr)
            process.check_returncode()
        output = process.stdout

    if expected_output is not None:
        assert output.strip() == expected_output

    return paths, output


def test_install_prefix(delete_files):
    check_output_from_shortcut(delete_files, "sys-prefix.json", expected_output=sys.prefix)


def test_precommands(delete_files):
    check_output_from_shortcut(
        delete_files, "precommands.json", expected_output="rhododendron and bees"
    )


@pytest.mark.skipif(PLATFORM != "osx", reason="macOS only")
def test_entitlements(delete_files):
    paths, _ = check_output_from_shortcut(
        delete_files, "entitlements.json", expected_output="entitlements"
    )
    # verify signature
    app_dir = next(p for p in paths if p.name.endswith(".app"))
    subprocess.check_call(["/usr/bin/codesign", "--verbose", "--verify", str(app_dir)])

    launcher = next(
        p for p in (app_dir / "Contents" / "MacOS").iterdir() if not p.name.endswith("-script")
    )
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
    paths, _ = check_output_from_shortcut(
        delete_files, "sys-prefix.json", expected_output=sys.prefix
    )
    app_dir = next(p for p in paths if p.name.endswith(".app"))
    launcher = next(
        p for p in (app_dir / "Contents" / "MacOS").iterdir() if not p.name.endswith("-script")
    )
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_call(["/usr/bin/codesign", "--verbose", "--verify", str(app_dir)])
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_call(["/usr/bin/codesign", "--verbose", "--verify", str(launcher)])


@pytest.mark.skipif(PLATFORM != "osx", reason="macOS only")
def test_info_plist(delete_files):
    paths, _ = check_output_from_shortcut(
        delete_files, "entitlements.json", expected_output="entitlements"
    )
    app_dir = next(p for p in paths if p.name.endswith(".app"))

    for path in app_dir.rglob("Info.plist"):
        plist = plistlib.loads(path.read_bytes())
        assert plist
        break
    else:
        raise AssertionError("Didn't find file")

    assert plist["LSEnvironment"]["example_var"] == "example_value"


@pytest.mark.skipif(PLATFORM != "osx", reason="macOS only")
def test_osx_symlinks(delete_files):
    paths, output = check_output_from_shortcut(delete_files, "osx_symlinks.json")
    app_dir = next(p for p in paths if p.name.endswith(".app"))
    symlinked_python = app_dir / "Contents" / "Resources" / "python"
    assert output.strip() == str(symlinked_python)
    assert symlinked_python.resolve() == (Path(DEFAULT_PREFIX) / "bin" / "python").resolve()


def test_file_type_association(delete_files):
    test_file = "test.csv"
    _, output = check_output_from_shortcut(
        delete_files,
        "file_types.json",
        action="open_file",
        file_to_open=test_file,
    )
    assert output.strip().endswith(test_file)


def test_url_protocol_association(delete_files):
    url = "menuinst://test"
    check_output_from_shortcut(
        delete_files,
        "url_protocols.json",
        action="open_url",
        url_to_open=url,
        expected_output=url,
    )
