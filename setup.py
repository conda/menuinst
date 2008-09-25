# Copyright (c) 2008 by Enthought, Inc.
# All rights reserved.


import sys

from setuptools import setup, Extension, find_packages


if sys.platform == "win32":
    win_libs = ["comctl32",  "kernel32", "user32", "gdi32", "winspool",
                "comdlg32", "advapi32", "shell32", "ole32", "oleaut32",
                "uuid", "odbc32", "odbccp32"]

    extensions = [Extension( "wininst.wininst",
                             sources = ["wininst/wininst.c"],
                             include_dirs = ["wininst"],
                             libraries = win_libs,
                             )]
else:
    extensions = []


setup( name = "wininst",
       version = "1.2.3",

       description  = "Python API used during windows installers",
       author       = "Greg Ward, Thomas Heller",
       author_email = "gward@python.net",
       url          = "http://www.python.org/sigs/distutils-sig",
       license      = "BSD",

       packages = find_packages(),
       include_package_data = True,
       zip_safe = False,
       ext_modules = extensions,
       package_data = {"wininst" : ["*.txt"],
                       },
       
       install_requires = [],
       extras_require = {},
       namespace_packages = [],
)
