# Copyright (c) 2008-2012 by Enthought, Inc.
# Copyright (c) 2013 Continuum Analytics, Inc.
# All rights reserved.
import sys
from distutils.core import Extension, setup

import versioneer

versioneer.versionfile_source = 'appinst/_version.py'
versioneer.versionfile_build = 'appinst/_version.py'
versioneer.tag_prefix = ''
versioneer.parentdir_prefix = 'appinst-'


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
    name = "appinst",
    version = versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description = "cross platform APIs to install applications menu items",
    ext_modules = extensions,
    include_package_data = True,
    package_data = {"appinst" : ["*.icns"]},
    license = "BSD",
    packages = ['appinst'],
)
