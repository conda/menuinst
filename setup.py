# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2013-2017 Continuum Analytics, Inc.
# Copyright (c) 2008-2011 by Enthought, Inc.
# All rights reserved.
#
# Licensed under the terms of the BSD 3-clause License (See LICENSE.txt)
# -----------------------------------------------------------------------------
"""Menuinst setup."""

# Standard library imports
from distutils.core import Extension, setup
import os
import sys

# Local imports
import versioneer


HERE = os.path.abspath(os.path.dirname(__file__))


def get_description():
    """Get long description."""
    with open(os.path.join(HERE, 'README.rst'), 'r') as f:
        data = f.read()
    return data


if sys.platform == "win32":
    extensions = [Extension(
            "menuinst.windows.winshortcut",
            sources=["menuinst/windows/winshortcut.cpp"],
            include_dirs=["menuinst"],
            libraries=["comctl32",  "kernel32", "user32", "gdi32", "winspool",
                       "comdlg32", "advapi32", "shell32", "ole32", "oleaut32",
                       "uuid", "odbc32", "odbccp32"]
            )]
    install_requires = ['pywin32']
else:
    extensions = []
    install_requires = []


setup(
    name="menuinst",
    url="https://github.com/ContinuumIO/menuinst",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="cross platform install of menu items",
    long_description=get_description(),
    ext_modules=extensions,
    include_package_data=True,
    install_requires=install_requires,
    package_data={"menuinst": ["osx/*.icns"]},
    license="BSD 3-clause",
    packages=[
        'menuinst',
        'menuinst.linux',
        'menuinst.osx',
        'menuinst.windows',
    ],
)
