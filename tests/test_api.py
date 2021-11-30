""""""
import os
import sys
import subprocess
from pathlib import Path
from time import sleep

import pytest
from conftest import DATA, PLATFORM


from menuinst.api import install


@pytest.mark.skipif(PLATFORM != "win", reason="Windows only")
def test_install_example_1_win(delete_files):
    paths = install(DATA / "jsons" / "example-1.json")
    lnk = next(p for p in paths if p.suffix == ".lnk")
    assert lnk.is_file()
    os.startfile(lnk)
    sleep(0.5)

    # TODO: Check output somehow... We will probably need to get
    # the target path of the lnk and launch that via subprocess


@pytest.mark.skipif(PLATFORM != "linux", reason="Linux only")
def test_install_example_1_linux(delete_files):
    paths = install(DATA / "jsons" / "example-1.json")
    desktop = next(p for p in paths if p.suffix == ".desktop")

    with open(desktop) as f:
        for line in f:
            if line.startswith("Exec="):
                target = line.split("=", 1)[1].strip()
                break
        else:
            raise ValueError("Didn't find Exec line")

    output = subprocess.check_output(target, shell=True, universal_newlines=True)
    assert output.strip() == os.path.join(sys.prefix, "bin", "python")


@pytest.mark.skipif(PLATFORM != "osx", reason="MacOS only")
def test_install_example_1_osx(delete_files):
    paths = install(DATA / "jsons" / "example-1.json")

    app_location = paths[0]
    output = subprocess.check_output(
        [str(app_location / "Contents" / "MacOS" / "Example")],
        universal_newlines=True,
    )
    assert output.strip() == os.path.join(sys.prefix, "bin", "python")

    delete_files.extend(paths)
