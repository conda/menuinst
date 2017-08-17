# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2013-2017 Continuum Analytics, Inc.
# Copyright (c) 2008-2011 by Enthought, Inc.
# All rights reserved.
#
# Licensed under the terms of the BSD 3-clause License (See LICENSE.txt)
# -----------------------------------------------------------------------------
"""OSX Menu and shortcut handling."""

# Standard library imports
import os
import plistlib
import shutil

# Local imports
from utils import rm_rf


class Menu(object):

    def __init__(self, unused_name, prefix, env_name, mode=None):
        self.prefix = prefix
        self.env_name = env_name

    def create(self):
        pass

    def remove(self):
        pass


class ShortCut(object):

    def __init__(self, menu, shortcut):
        self.shortcut = shortcut
        self.prefix = menu.prefix
        self.name = shortcut['name']
        self.path = '/Applications/%s.app' % self.name
        self.shortcut = shortcut

    def remove(self):
        rm_rf(self.path)

    def create(self):
        Application(self.path, self.shortcut, self.prefix).create()


class Application(object):
    """
    Class for creating an application folder on OSX.  The application may
    be standalone executable, but more likely a Python script which is
    interpreted by the framework Python interpreter.
    """
    def __init__(self, app_path, shortcut, prefix, env_name, env_setup_cmd):
        """
        Required:
        ---------
        shortcut is a dictionary defining a shortcut per the AppInst standard.
        """
        # Store the required values out of the shortcut definition.
        self.app_path = app_path
        self.prefix = prefix
        self.name = shortcut['name']
        self.cmd = shortcut['cmd']
        self.icns = shortcut['icns']
        self.env_name = env_name
        self.env_setup_cmd = env_setup_cmd


        for a, b in [
            ('${BIN_DIR}', os.path.join(prefix, 'bin')),
            ('${MENU_DIR}', os.path.join(prefix, 'Menu')),
            ]:
            self.cmd = self.cmd.replace(a, b)
            self.icns = self.icns.replace(a, b)

        # Calculate some derived values just once.
        self.contents_dir = os.path.join(self.app_path, 'Contents')
        self.resources_dir = os.path.join(self.contents_dir, 'Resources')
        self.macos_dir = os.path.join(self.contents_dir, 'MacOS')
        self.executable = self.name
        self.executable_path = os.path.join(self.macos_dir, self.executable)

    def create(self):
        self._create_dirs()
        self._write_pkginfo()
        shutil.copy(self.icns, self.resources_dir)
        self._writePlistInfo()
        self._write_script()

    def _create_dirs(self):
        rm_rf(self.app_path)
        os.makedirs(self.resources_dir)
        os.makedirs(self.macos_dir)

    def _write_pkginfo(self):
        fo = open(os.path.join(self.contents_dir, 'PkgInfo'), 'w')
        fo.write(('APPL%s????' % self.name.replace(' ', ''))[:8])
        fo.close()

    def _writePlistInfo(self):
        """
        Writes the Info.plist file in the Contests directory.
        """
        pl = plistlib.Plist(
            CFBundleExecutable=self.executable,
            CFBundleGetInfoString='%s-1.0.0' % self.name,
            CFBundleIconFile=os.path.basename(self.icns),
            CFBundleIdentifier='com.%s' % self.name,
            CFBundlePackageType='APPL',
            CFBundleVersion='1.0.0',
            CFBundleShortVersionString='1.0.0',
            )
        plistlib.writePlist(pl, os.path.join(self.contents_dir, 'Info.plist'))

    def _write_script(self):
        fo = open(self.executable_path, 'w')
        fo.write( """\
#!/bin/bash
%s/python.app/Contents/MacOS/python %s
""" % (self.prefix, self.cmd))
        fo.close()
        os.chmod(self.executable_path, 0o755)


if __name__ == '__main__':
    sc = {
        "name": "Launcher",
        "cmd": "${BIN_DIR}/launcher",
        "icns": "${MENU_DIR}/launcher.icns",
    }
    ShortCut(None, sc).remove()
