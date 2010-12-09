# Copyright (c) 2008-2009 by Enthought, Inc.
# All rights reserved.


import sys

from setuptools import Extension, find_packages, setup


if sys.platform == "win32":
    win_libs = ["comctl32",  "kernel32", "user32", "gdi32", "winspool",
        "comdlg32", "advapi32", "shell32", "ole32", "oleaut32", "uuid",
        "odbc32", "odbccp32"]
    extensions = [Extension("appinst.platforms.wininst",
        sources = ["appinst/platforms/wininst.c"],
        include_dirs = ["appinst/platforms"],
        libraries = win_libs,
        )]
    install_requires = [
        'pywin32',
        ]
else:
    extensions = []
    install_requires = []


setup(
    author = "Greg Ward, Thomas Heller",
    author_email = "gward@python.net",
    description = "Cross platform APIs used to install applications",
    extras_require = {},
    ext_modules = extensions,
    include_package_data = True,
    install_requires = install_requires,
    license = "BSD",
    maintainer = "Enthought, Inc.",
    maintainer_email = "info@enthought.com",
    name = "AppInst",
    namespace_packages = [],
    packages = find_packages(),
    package_data = {"appinst" : ["*.txt", "platforms/*.icns"], },
    version = "2.0.5",
    url = "http://www.python.org/sigs/distutils-sig",
    zip_safe = False,
)
