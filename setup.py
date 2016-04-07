# Copyright (c) 2008-2012 by Enthought, Inc.
# Copyright (c) 2013 Continuum Analytics, Inc.
# All rights reserved.
import sys
from distutils.core import Extension, setup

import versioneer


if sys.platform == "win32":
    extensions = [Extension(
            "menuinst.winshortcut",
            sources=["menuinst/winshortcut.cpp"],
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
    name = "menuinst",
    url = "https://github.com/ContinuumIO/menuinst",
    version = versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description = "cross platform install of menu items",
    long_description = open('README.rst').read(),
    ext_modules = extensions,
    include_package_data = True,
    install_requires = install_requires,
    package_data = {"menuinst" : ["*.icns"]},
    license = "BSD",
    packages = ['menuinst'],
)
