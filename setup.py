# Copyright (c) 2008-2012 by Enthought, Inc.
# Copyright (c) 2013 Continuum Analytics, Inc.
# All rights reserved.
import sys

from setuptools import Extension, setup

extensions = []
if sys.platform == "win32":
    extensions.append(
        Extension(
            "menuinst.platforms.win_utils.winshortcut",
            sources=["src/winshortcut.cpp"],
            include_dirs=["src/"],
            libraries=[
                "comctl32",
                "kernel32",
                "user32",
                "gdi32",
                "winspool",
                "comdlg32",
                "advapi32",
                "shell32",
                "ole32",
                "oleaut32",
                "uuid",
                "odbc32",
                "odbccp32",
            ],
        )
    )


setup(ext_modules=extensions)
