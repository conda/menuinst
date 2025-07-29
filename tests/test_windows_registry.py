import os
import time
from pathlib import Path
import logging

import pytest

registry = pytest.importorskip("menuinst.platforms.win_utils.registry")


def test_file_extensions(tmp_path: Path, request):
    """
    We will register a custom, random extension.
    The command will only echo the input path to a known output location.
    After "opening" an empty file with that extension, the output file
    should contain the file path we opened!

    We then clean up and make sure that opening that file doesn't
    create the output file.
    """
    name = str(hash(str(tmp_path)))[:6]
    extension = f".menuinst-{name}"
    identifier = f"menuinst.assoc.menuinst-{name}"

    def cleanup():
        # This key is not normally cleaned up because another programs might
        # be using it, but since we know these are synthetic and made up,
        # we try not to pollute the registry too much
        registry._reg_exe("delete", rf"HKCU\Software\Classes\.menuinst-{name}")

    request.addfinalizer(cleanup)

    registry.register_file_extension(
        extension=extension,
        identifier=identifier,
        command=rf'cmd.exe /Q /D /V:ON /C "echo %1>{tmp_path}\output.txt"',
        mode="user",
    )
    input_file = tmp_path / f"input.menuinst-{name}"
    output_file = tmp_path / "output.txt"
    try:
        input_file.touch()
        os.startfile(input_file)
        t0 = time.time()
        while time.time() - t0 <= 10:  # wait 10 seconds
            try:
                assert output_file.read_text().strip() == str(input_file)
            except IOError:
                time.sleep(1)
        if not output_file.exists():
            raise AssertionError("Output file was never created")
    finally:
        registry.unregister_file_extension(extension=extension, identifier=identifier, mode="user")

    output_file.unlink()
    os.startfile(input_file)  # this will raise UI if not headless, ignore
    t0 = time.time()
    while time.time() - t0 <= 3:  # wait up to 3 seconds
        time.sleep(1)
        assert not output_file.exists()


def test_unregister_file_extension_error(capsys, request):
    """
    Unregister a file extension that has not been registered and check that the
    appropriate log message is reported.
    """
    def cleanup():
        registry.log.handlers.clear()
        registry.log.setLevel(logging.NOTSET)

    request.addfinalizer(cleanup)

    registry.log.addHandler(logging.StreamHandler())
    registry.log.setLevel("DEBUG")

    identifier = "menuinst.assoc.menuinst-foo"

    registry.unregister_file_extension(
        extension=".menuinst-bar", identifier=identifier, mode="user"
    )
    captured = capsys.readouterr()
    assert captured.err.strip() == "Handler 'menuinst.assoc.menuinst-foo' is not associated with extension '.menuinst-bar'"


def test_protocols(tmp_path):
    """
    We will register a custom, random protocol.
    The command will only echo the input path to a known output location.
    After "opening" a fake URL with that protocol, the output file
    should contain the file path we opened!

    We then clean up and make sure that opening that file doesn't
    create the output file.
    """
    name = str(hash(str(tmp_path)))[:6]
    registry.register_url_protocol(
        protocol=f"menuinst-{name}",
        command=rf'cmd.exe /Q /D /V:ON /C "echo %1>{tmp_path}\output.txt"',
        identifier=f"menuinst.protocol.menuinst-{name}",
        mode="user",
    )
    input_url = f"menuinst-{name}://fake-value"
    output_file = tmp_path / "output.txt"
    os.startfile(input_url)
    try:
        t0 = time.time()
        while time.time() - t0 <= 10:  # wait 10 seconds
            try:
                assert output_file.read_text().strip().rstrip("/") == input_url.rstrip("/")
            except IOError:
                time.sleep(1)
        if not output_file.exists():
            raise AssertionError("Output file was never created")
    finally:
        registry.unregister_url_protocol(
            protocol=f"menuinst-{name}",
            identifier=f"menuinst.protocol.menuinst-{name}",
            mode="user",
        )

    output_file.unlink()
    os.startfile(input_url)  # this will raise UI if not headless, ignore
    t0 = time.time()
    while time.time() - t0 <= 3:  # wait up to 3 seconds
        time.sleep(1)
        assert not output_file.exists()
