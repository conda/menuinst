"""
    Tests for specific functions in the utils package.
"""
from menuinst.utils import WinLex


def test_quote_args_1():
    """ Verify the input arguments are quoted. """
    wl = WinLex()
    test_str = [r"%SystemRoot%\system32\foo.exe", "/pt", "%1", "%2", "%3", "%4"]
    output = wl.quote_args(test_str)
    assert output == [
        '%SystemRoot%\\system32\\foo.exe',
        '"/pt"',
        '"%1"',
        '"%2"',
        '"%3"',
        '"%4"'
    ]

def test_quote_args_2():
    """ Verify correct quotes with blank spaces. """
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
    """ Verify special case with cmd.exe and /C. """
    args = ["cmd.exe", "/C", "echo", "Hello World"]
    wl = WinLex()
    output = wl.quote_args(args)
    assert output == [
        '"cmd.exe"',
        '/C',
        '""echo" "Hello World""'
    ]
