# Copyright (c) 2008-2011 by Enthought, Inc.
# All rights reserved.
import sys
from setuptools import Extension, setup


if sys.platform == "win32":
    extensions = [Extension(
            "appinst.wininst",
            sources=["appinst/wininst.c"],
            include_dirs=["appinst"],
            libraries=["comctl32",  "kernel32", "user32", "gdi32", "winspool",
                       "comdlg32", "advapi32", "shell32", "ole32", "oleaut32",
                       "uuid", "odbc32", "odbccp32"]
            )]
else:
    extensions = []


setup(
    name = "AppInst",
    version = "2.1.0",
    description = "Cross platform APIs used to install applications",
    ext_modules = extensions,
    include_package_data = True,
    package_data = {"appinst" : ["*.icns"]},
    license = "BSD",
    maintainer = "Enthought, Inc.",
    maintainer_email = "info@enthought.com",
    packages = ['appinst'],
    zip_safe = False,
)
