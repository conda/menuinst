"""
Tests for specific functions in the utils package.
"""

from menuinst.utils import WinLex


def test_quote_args_1():
    """Verify the input arguments are quoted."""
    wl = WinLex()
    test_str = [r"%SystemRoot%\system32\foo.exe", "/pt", "%1", "%2", "%3", "%4"]
    output = wl.quote_args(test_str)
    assert output == [r'"%SystemRoot%\system32\foo.exe"', '"/pt"', '"%1"', '"%2"', '"%3"', '"%4"']


def test_quote_args_2():
    """Verify correct quotes with blank spaces."""
    wl = WinLex()
    args = [
        r"C:\Windows\System32\notepad.exe",
        "/pt",
        r"C:\Users\Foo Bar\file.txt",
        "HP LaserJet",
    ]
    output = wl.quote_args(args)
    assert output == [
        r"C:\Windows\System32\notepad.exe",
        '"/pt"',
        r'"C:\Users\Foo Bar\file.txt"',
        '"HP LaserJet"',
    ]


def test_quote_args_3():
    """Verify special case with cmd.exe and /C."""
    args = ["cmd.exe", "/C", "echo", "Hello World"]
    wl = WinLex()
    output = wl.quote_args(args)
    assert output == ["cmd.exe", "/C", '"echo "Hello World""']


def test_quote_args_4():
    """Verify special case with cmd.exe and /K many words with spaces and percentage signs."""
    args = ["cmd.exe", "/K", "dir", "Hello World", "%1 %2 %foo% with spaces", "x", "y"]
    wl = WinLex()
    output = wl.quote_args(args)
    assert output == ["cmd.exe", "/K", '"dir "Hello World" "%1 %2 %foo% with spaces" x y"']


def test_quote_args_5():
    """Verify special case with spaces, cmd.exe and /K and percentage signs."""
    args = [
        r"C:\path with spaces\cmd.exe",
        "/K",
        "dir",
        "Hello World",
        "%1 %2 %foo% with spaces",
        "x",
        "y",
    ]
    wl = WinLex()
    output = wl.quote_args(args)
    assert output == [
        r'"C:\path with spaces\cmd.exe"',
        "/K",
        '"dir "Hello World" "%1 %2 %foo% with spaces" x y"',
    ]
