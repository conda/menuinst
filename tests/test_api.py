""""""
import os
import plistlib
import shlex
import subprocess
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import sleep, time
from typing import Iterable, Tuple

import pytest
from conftest import DATA, PLATFORM

from menuinst.api import install, remove
from menuinst.platforms.osx import _lsregister
from menuinst.utils import DEFAULT_PREFIX, logged_run


def _poll_for_file_contents(path, timeout=10):
    t0 = time()
    while not os.path.isfile(path):
        sleep(1)
        if time() >= t0 + timeout / 2:
            raise RuntimeError(f"Timeout. File '{path}' was not created!")
    out = ""
    while not out:
        out = Path(path).read_text()
        sleep(1)
        if time() >= t0 + timeout:
            raise RuntimeError(f"Timeout. File '{path}' was empty!")
    return out


def check_output_from_shortcut(
    delete_files,
    json_path,
    remove_after=True,
    expected_output=None,
    action="run_shortcut",
    file_to_open=None,
    url_to_open=None,
) -> Tuple[Path, Iterable[Path], str]:
    assert action in ("run_shortcut", "open_file", "open_url")

    output_file = None
    abs_json_path = DATA / "jsons" / json_path
    contents = abs_json_path.read_text()
    if "__OUTPUT_FILE__" in contents:
        with NamedTemporaryFile(suffix=json_path, mode="w", delete=False) as tmp:
            output_file = str(Path(tmp.name).resolve()) + ".out"
            contents = contents.replace("__OUTPUT_FILE__", output_file.replace("\\", "\\\\"))
            tmp.write(contents)
        abs_json_path = tmp.name
        delete_files.append(abs_json_path)

    paths = install(abs_json_path)
    delete_files += list(paths)

    try:
        if action == "run_shortcut":
            if PLATFORM == "win":
                lnk = next(p for p in paths if p.suffix == ".lnk")
                assert lnk.is_file()
                os.startfile(lnk)
                output = _poll_for_file_contents(output_file)
            else:
                if PLATFORM == "linux":
                    desktop = next(p for p in paths if p.suffix == ".desktop")
                    with open(desktop) as f:
                        for line in f:
                            if line.startswith("Exec="):
                                cmd = shlex.split(line.split("=", 1)[1].strip())
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
                    cmd = [str(executable)]
                process = logged_run(cmd, check=True)
                output = process.stdout
        else:
            if action == "open_file":
                assert file_to_open is not None
                with NamedTemporaryFile(suffix=file_to_open, delete=False) as f:
                    # file cannot be empty; otherwise mimetype detection fails on Linux
                    f.write(b"1234")
                delete_files.append(f.name)
                arg = f.name
            elif action == "open_url":
                assert url_to_open is not None
                arg = url_to_open
            app_location = paths[0]
            cmd = {
                "linux": ["xdg-open"],
                # FIXME: Should work WITHOUT -a <app_location>
                # "osx": ["open"],
                "osx": ["open", "-a", str(app_location)],
                "win": ["cmd", "/C", "start"],
            }[PLATFORM]
            process = logged_run([*cmd, arg], check=True)
            output = _poll_for_file_contents(output_file)
    finally:
        if remove_after:
            remove(abs_json_path)
        if action in ("open_file", "open_url") and PLATFORM == "osx":
            _lsregister(
                "-kill", "-r", "-domain", "local", "-domain", "user", "-domain", "system"
            )
            assert "menuinst" not in _lsregister("-dump", log=False).stdout

    if expected_output is not None:
        assert output.strip() == expected_output

    return abs_json_path, paths, output


def test_install_prefix(delete_files):
    check_output_from_shortcut(delete_files, "sys-prefix.json", expected_output=sys.prefix)


def test_precommands(delete_files):
    check_output_from_shortcut(
        delete_files, "precommands.json", expected_output="rhododendron and bees"
    )


@pytest.mark.skipif(PLATFORM != "osx", reason="macOS only")
def test_entitlements(delete_files):
    json_path, paths, _ = check_output_from_shortcut(
        delete_files, "entitlements.json", remove_after=False, expected_output="entitlements"
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

    remove(json_path)


@pytest.mark.skipif(PLATFORM != "osx", reason="macOS only")
def test_no_entitlements_no_signature(delete_files):
    json_path, paths, _ = check_output_from_shortcut(
        delete_files, "sys-prefix.json", remove_after=False, expected_output=sys.prefix
    )
    app_dir = next(p for p in paths if p.name.endswith(".app"))
    launcher = next(
        p for p in (app_dir / "Contents" / "MacOS").iterdir() if not p.name.endswith("-script")
    )
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_call(["/usr/bin/codesign", "--verbose", "--verify", str(app_dir)])
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_call(["/usr/bin/codesign", "--verbose", "--verify", str(launcher)])
    remove(json_path)


@pytest.mark.skipif(PLATFORM != "osx", reason="macOS only")
def test_info_plist(delete_files):
    json_path, paths, _ = check_output_from_shortcut(
        delete_files, "entitlements.json", remove_after=False, expected_output="entitlements"
    )
    app_dir = next(p for p in paths if p.name.endswith(".app"))

    for path in app_dir.rglob("Info.plist"):
        plist = plistlib.loads(path.read_bytes())
        assert plist
        break
    else:
        raise AssertionError("Didn't find file")

    assert plist["LSEnvironment"]["example_var"] == "example_value"

    remove(json_path)


@pytest.mark.skipif(PLATFORM != "osx", reason="macOS only")
def test_osx_symlinks(delete_files):
    json_path, paths, output = check_output_from_shortcut(
        delete_files, "osx_symlinks.json", remove_after=False
    )
    app_dir = next(p for p in paths if p.name.endswith(".app"))
    symlinked_python = app_dir / "Contents" / "Resources" / "python"
    assert output.strip() == str(symlinked_python)
    assert symlinked_python.resolve() == (Path(DEFAULT_PREFIX) / "bin" / "python").resolve()
    remove(json_path)


def test_file_type_association(delete_files):
    test_file = "test.menuinst"
    *_, output = check_output_from_shortcut(
        delete_files,
        "file_types.json",
        action="open_file",
        file_to_open=test_file,
    )
    assert output.strip().endswith(test_file)


def test_url_protocol_association(delete_files):
    url = "menuinst://test/"
    check_output_from_shortcut(
        delete_files,
        "url_protocols.json",
        action="open_url",
        url_to_open=url,
        expected_output=url,
    )
