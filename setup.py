# Copyright (c) 2008-2012 by Enthought, Inc.
# Copyright (c) 2013 Continuum Analytics, Inc.
# All rights reserved.
import sys
from setuptools import find_packages, Extension, setup
from pathlib import Path

import versioneer


install_requires = ["typing_extensions"]
if sys.platform == "win32":
    extensions = [
        Extension(
            "menuinst._legacy.winshortcut",
            sources=["menuinst/_legacy/winshortcut.cpp"],
            include_dirs=["menuinst/_legacy"],
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
    ]
else:
    extensions = []


setup(
    name="menuinst",
    url="https://github.com/conda/menuinst",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="cross platform install of menu items",
    long_description=Path("README.rst").read_text(),
    ext_modules=extensions,
    include_package_data=True,
    package_data = {"menuinst" : ["*.icns"]},
    install_requires=install_requires,
    license="BSD",
    packages=find_packages(exclude=("tests", "tests.*")),
)
