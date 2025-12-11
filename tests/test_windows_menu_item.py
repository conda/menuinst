import os
import subprocess
from pathlib import Path

import pytest
from conftest import PLATFORM
from tpying import TYPE_CHECKING

pytestmark = pytest.mark.skipif(
    PLATFORM != "win", reason="This file contains tests that are Windows only."
)

# These imports don't execute at runtime → no E402 issues
if TYPE_CHECKING:
    from menuinst.platforms.win import WindowsMenu, WindowsMenuItem
    from menuinst.utils import WinLex
else:
    WindowsMenu = pytest.importorskip("menuinst.platforms.win").WindowsMenu
    WindowsMenuItem = pytest.importorskip("menuinst.platforms.win").WindowsMenuItem
    WinLex = pytest.importorskip("menuinst.utils").WinLex

# DEFAULT_PATH is actually not used to write any actual file,
# just to mimic a real path
DEFAULT_PATH = Path(os.environ.get("TEMP", os.getcwd()))


"""
    The purpose of DummyWindowsMenuItem, Dummy is to enable unit testing of WindowsMenuItem
    without the full menu suite. In particular we verify below that processed commands are quoted
    properly and can execute.
"""


class DummyWindowsMenuItem(WindowsMenuItem):
    def _write_script(self, **kwargs) -> Path:
        return DEFAULT_PATH / Path("dummy_script.bat")


class Dummy(WindowsMenu):
    """This is a dummy class only used for testing WindowsMenuItem.
    It's bare-minimum in order to perform simple testing.
    """

    def _is_micromamba(self, foo):
        False

    conda_exe = ""
    prefix = "prefix"
    start_menu_location = DEFAULT_PATH


def create_test_menu_item(
    command: list[str], activate: bool = False, terminal: bool = False
) -> DummyWindowsMenuItem:
    return DummyWindowsMenuItem(
        Dummy("foo"),
        {"activate": activate, "name": "foo", "command": command, "terminal": terminal},
    )


@pytest.mark.skipif(PLATFORM != "win", reason="Windows only")
@pytest.mark.parametrize("with_arg1", (True, False))
def test_process_command(with_arg1):
    wmi = create_test_menu_item(["hello", "world"], activate=False, terminal=False)

    expected = ["hello", "world"]
    if with_arg1:
        expected.append('"%1')
    assert wmi._process_command(with_arg1), expected


@pytest.mark.skipif(PLATFORM != "win", reason="Windows only")
@pytest.mark.parametrize("with_arg1", (True, False))
def test_process_command_with_spaces(with_arg1):
    wmi = create_test_menu_item(
        ["C:\\S p a c e s\\cmd.exe", "/D", "hello", "world"], activate=False, terminal=False
    )

    expected = ['"C:\\S p a c e s\\cmd.exe"', "/D", "hello", "world"]
    if with_arg1:
        expected.append('"%1')
    assert wmi._process_command(with_arg1), expected


@pytest.mark.skipif(PLATFORM != "win", reason="Windows only")
@pytest.mark.parametrize("with_arg1", (True, False))
def test_process_command_as_activated(with_arg1):
    wmi = create_test_menu_item(["unnecessary"], activate=True, terminal=False)

    expected = [
        "C:\\Windows\\system32\\cmd.exe",
        "/D",
        "/C",
        "START",
        "/MIN",
        '""',
        "C:\\Windows\\system32\\WindowsPowerShell\\v1.0\\powershell.exe",
        "-WindowStyle",
        "hidden",
        "start",
        str(DEFAULT_PATH / "dummy_script.bat"),
    ]
    if with_arg1:
        expected.append('"%1')
    expected += ["-WindowStyle", "hidden"]
    assert wmi._process_command(with_arg1), expected


@pytest.mark.skipif(PLATFORM != "win", reason="Windows only")
@pytest.mark.parametrize("with_arg1", (True, False))
def test_process_command_as_activated_and_terminal(with_arg1):
    wmi = create_test_menu_item(["unnecessary"], activate=True, terminal=True)

    expected = ["cmd", "/D", "/K", str(DEFAULT_PATH / "dummy_script.bat")]
    if with_arg1:
        expected.append('"%1')
    assert wmi._process_command(with_arg1), expected


@pytest.mark.skipif(PLATFORM != "win", reason="Windows only")
def test_run_generated_command(tmp_path):
    """This test does several thing to mimic in-production use of WindowsMenuItems.
    * Create a command, containing spaces, metachars and environment variables.
    * Verify command is generated correctly.
    * Run generated command and verify the command executed as expected.
    """
    test_file = tmp_path / "my file.txt"
    test_env_variable = "FOOBAR"
    test_string = "test string"
    wmi = create_test_menu_item(
        ["cmd.exe", "/C", "echo", "%FOOBAR%", ">", str(test_file)], activate=False, terminal=False
    )

    test_environment = os.environ.copy()
    test_environment[test_env_variable] = test_string
    wl = WinLex()
    cmdline = " ".join(wl.quote_args(wmi._process_command(False)))

    expected_cmdline = f'cmd.exe /C ""echo %FOOBAR% > "{test_file}"""'
    assert cmdline == expected_cmdline

    p = subprocess.run(cmdline, shell=True, env=test_environment)
    assert p.returncode == 0
    assert test_file.exists()
    with open(test_file, "r") as f:
        contents = f.readlines()
    assert contents[0].strip() == test_string
