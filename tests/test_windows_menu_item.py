import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from conftest import PLATFORM

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
@pytest.mark.parametrize(
    "conda_exe_path,prefix_path",
    [
        (r"C:\Program Files\FooBar\conda.exe", r"C:\Program Files\FooBar"),
        (r"C:\FooBar 123\base\_conda.exe", r"C:\FooBar 123\base"),
        (r"C:\path with spaces\conda.exe", r"C:\path with spaces\envs\test"),
    ],
)
def test_command_quotes_paths_with_spaces(conda_exe_path, prefix_path, monkeypatch, tmp_path):
    """Test that _command() properly quotes conda_exe and prefix paths containing spaces.

    Regression test for installation paths that contain spaces.
    Without proper quoting, batch files would fail with:
    'C:\\path\\FooBar' is not recognized as an internal or external command
    """
    from menuinst.platforms import win as win_module

    # Create a fake .env file
    fake_env_file = tmp_path / "activate.env"
    fake_env_content = f"_CONDA_SCRIPT={prefix_path}\\Scripts\\activate.bat\nCONDA_PREFIX={prefix_path}"
    fake_env_file.write_text(fake_env_content)

    # Create a menu item with activate=True to trigger the activation code path
    class TestMenu(WindowsMenu):
        def __init__(self):
            self.mode = "user"
            self.name = "Test"
            self.prefix = Path(prefix_path)
            self.base_prefix = Path(prefix_path).parent
            self.env_name = "test"
            self._conda_exe = Path(conda_exe_path)

        @property
        def conda_exe(self):
            return self._conda_exe

        def _is_micromamba(self, exe):
            return False

        def render(self, value, slug=False, extra=None):
            return value

    menu = TestMenu()
    metadata = {
        "activate": True,
        "terminal": False,
        "name": "Test App",
        "command": ["python", "-c", "print('hello')"],
        "precommand": None,
    }

    item = WindowsMenuItem(menu, metadata)

    # Mock logged_run to return the fake .env file path
    class FakeRunResult:
        stdout = str(fake_env_file)

    monkeypatch.setattr(win_module, "logged_run", lambda *args, **kwargs: FakeRunResult())

    # Generate the command
    command = item._command()

    # Verify that paths with spaces are quoted in the generated batch script
    lines = command.split("\r\n")

    # Find the @CALL line for _CONDA_SCRIPT
    call_lines = [l for l in lines if l.startswith("@CALL")]
    assert len(call_lines) >= 1, f"Expected @CALL line in command, got: {lines}"

    # The path in @CALL should be quoted if it contains spaces
    if " " in prefix_path:
        call_line = call_lines[0]
        # The path should be wrapped in quotes
        assert f'"{prefix_path}' in call_line or f'@CALL "' in call_line, (
            f"Path with spaces should be quoted in @CALL. Got: {call_line}"
        )


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
