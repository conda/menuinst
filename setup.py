# Copyright (c) 2008 by Enthought, Inc.
# All rights reserved.


import sys

from setuptools import setup, Extension, find_packages


if sys.platform == "win32":
    win_libs = ["comctl32",  "kernel32", "user32", "gdi32", "winspool",
                "comdlg32", "advapi32", "shell32", "ole32", "oleaut32",
                "uuid", "odbc32", "odbccp32"]

    extensions = [Extension( "appinst.appinst",
                             sources = ["appinst/appinst.c"],
                             include_dirs = ["appinst"],
                             libraries = win_libs,
                             )]
else:
    extensions = []


setup(
    author = "Greg Ward, Thomas Heller",
    author_email = "gward@python.net",
    description = "Python API used during windows installers",
    extras_require = {},
    ext_modules = extensions,
    include_package_data = True,
    install_requires = [],
    license = "BSD",
    maintainer = "Enthought, Inc.",
    maintainer_email = "info@enthought.com",
    name = "AppInst",
    namespace_packages = [],
    packages = find_packages(),
    package_data = {"appinst" : ["*.txt"], },
    version = "1.2.3",
    url = "http://www.python.org/sigs/distutils-sig",
    zip_safe = False,
    )

