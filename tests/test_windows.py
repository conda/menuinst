import os
import sys
import time
from pathlib import Path

import pytest

registry = pytest.importorskip("menuinst.platforms.win_utils.registry")


def test_file_extensions(tmp_path: Path):
    """
    We will register a custom, random extension.
    The command will only echo the input path to a known output location.
    After "opening" an empty file with that extension, the output file
    should contain the file path we opened!

    We then clean up and make sure that opening that file doesn't
    create the output file.
    """
    name = tmp_path.name
    registry.register_file_extension(
        extension=f".menuinst-{name}", 
        identifier=f"menuinst.assoc.menuinst-{name}",
        command=fr'cmd.exe /Q /D /V:ON /C "echo %1>{tmp_path}\output.txt"',
        mode="user",
    )
    input_file = tmp_path / f"input.menuinst-{name}"
    output_file = tmp_path / "output.txt"
    input_file.touch()
    os.startfile(input_file)
    try:
        t0 = time.time()
        while time.time() - t0 <= 10:  # wait 10 seconds
            try:
                assert output_file.read_text().strip() == str(input_file)
            except IOError:
                time.sleep(1)
        if not output_file.exists():
            raise AssertionError("Output file was never created")
    finally:
        registry.unregister_file_extension(
            extension=f".menuinst-{name}", 
            identifier=f"menuinst.assoc.menuinst-{name}",
            mode="user"
        )

    output_file.unlink()
    os.startfile(input_file)  # this will raise UI if not headless, ignore
    t0 = time.time()
    while time.time() - t0 <= 3:  # wait up to 3 seconds
        time.sleep(1)
        assert not output_file.exists()


def test_protocols():
    pass
