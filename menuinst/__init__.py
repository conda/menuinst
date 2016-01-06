# Copyright (c) 2008-2011 by Enthought, Inc.
# Copyright (c) 2013-2015 Continuum Analytics, Inc.
# All rights reserved.

from __future__ import absolute_import
import sys
import json
import subprocess
import tempfile
from os.path import abspath, basename, exists, join

from ._version import get_versions
__version__ = get_versions()['version']

if sys.platform.startswith('linux'):
    from .linux import Menu, ShortCut

elif sys.platform == 'darwin':
    from .darwin import Menu, ShortCut

elif sys.platform == 'win32':
    from .win32 import Menu, ShortCut


DEBUG = 0


def elevated_install(path, remove, prefix):
    tmp_dir = tempfile.mkdtemp()
    if DEBUG:
        sys.stdout.write('MENU-TMP_DIR: %s' % tmp_dir)
    py_path = join(tmp_dir, 'menu.py')
    bat_path = join(tmp_dir, 'menu.bat')

    with open(py_path, 'w') as fo:
        fo.write("""\
import menuinst
menuinst._install(%r, %r, %r)
""" % (path, bool(remove), prefix))

# http://stackoverflow.com/questions/4051883/batch-script-how-to-check-for-admin-rights
# Quick test for Windows generation: UAC aware or not ; all OS before NT4 ignored for simplicity
    with open(bat_path, 'w') as fo:
        fo.write(r"""@setlocal enableextensions enabledelayedexpansion
@echo off

SET "PYTHON=@@SYSPREFIX@@\pythonw.exe"
SET "SCRIPT=@@PY_PATH@@"

SET NewOSWith_UAC=YES
VER | FINDSTR /IL "5." > NUL
IF %ERRORLEVEL% == 0 SET NewOSWith_UAC=NO
VER | FINDSTR /IL "4." > NUL
IF %ERRORLEVEL% == 0 SET NewOSWith_UAC=NO

REM Test if Admin
IF /i "%NewOSWith_UAC%"=="YES" (
    CALL NET SESSION >nul 2>&1
    IF NOT %ERRORLEVEL% == 0 (
        echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
        echo UAC.ShellExecute "%PYTHON%", "%SCRIPT%", "", "runas", 1 >> "%temp%\getadmin.vbs"
        "%SystemRoot%\System32\WScript.exe" "%temp%\getadmin.vbs"
        del "%temp%\getadmin.vbs"
    ) ELSE (
        REM  Already elevated.  Just run the script.
       "%PYTHON%" "%SCRIPT%"
    )
) ELSE (
    REM  Already elevated.  Just run the script.
    "%PYTHON%" "%SCRIPT%"
)

endlocal
""".replace('@@SYSPREFIX@@', sys.prefix).replace('@@PY_PATH@@', py_path))

    subprocess.check_call([bat_path])


def _install(path, remove=False, prefix=sys.prefix):
    if abspath(prefix) == abspath(sys.prefix):
        env_name = None
        env_setup_cmd = None
    else:
        env_name = basename(prefix)
        env_setup_cmd = 'activate "%s"' % env_name

    data = json.load(open(path))
    try:
        menu_name = data['menu_name']
    except KeyError:
        menu_name = 'Python-%d.%d' % sys.version_info[:2]

    shortcuts = data['menu_items']
    m = Menu(menu_name)
    if remove:
        for sc in shortcuts:
            ShortCut(m, sc,
                     target_prefix=prefix, env_name=env_name,
                     env_setup_cmd=env_setup_cmd).remove()
        m.remove()
    else:
        m.create()
        for sc in shortcuts:
            ShortCut(m, sc,
                     target_prefix=prefix, env_name=env_name,
                     env_setup_cmd=env_setup_cmd).create()


def install(path, remove=False, prefix=sys.prefix):
    """
    install Menu and shortcuts
    """
    if sys.platform == 'win32' and not exists(join(sys.prefix, '.nonadmin')):
        elevated_install(path, remove, prefix)
    else:
        _install(path, remove, prefix)


from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
