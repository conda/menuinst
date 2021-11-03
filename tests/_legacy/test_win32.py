# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
from logging import getLogger

from menuinst.win32 import quote_args

log = getLogger(__name__)


def test_quote_args_1():
    args = [
        "%windir%\\System32\\cmd.exe",
        "/K",
        "c:\\Users\\Francisco García Carrión Martínez\\Anaconda 3\\Scripts\\activate.bat",
        "c:\\Users\\Francisco García Carrión Martínez\\Anaconda 3",
    ]
    assert quote_args(args) == [
        "\"%windir%\\System32\\cmd.exe\"",
        "/K",
        "\"\"c:\\Users\\Francisco García Carrión Martínez\\Anaconda 3\\Scripts\\activate.bat\" \"c:\\Users\\Francisco García Carrión Martínez\\Anaconda 3\"\"",
    ]
