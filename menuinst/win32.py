# Copyright (c) 2008-2011 by Enthought, Inc.
# Copyright (c) 2013 Continuum Analytics, Inc.
# All rights reserved.

from __future__ import absolute_import

import os
import sys
from os.path import expanduser, isdir, join, exists

from .utils import rm_empty_dir, rm_rf
from .csidl import get_folder_path
from .winshortcut import create_shortcut

mode = ('user' if exists(join(sys.prefix, '.nonadmin')) else 'system')

quicklaunch_dir = join(get_folder_path('CSIDL_APPDATA'),
                       "Microsoft", "Internet Explorer", "Quick Launch")

if mode == 'system':
    desktop_dir = get_folder_path('CSIDL_COMMON_DESKTOPDIRECTORY')
    start_menu = get_folder_path('CSIDL_COMMON_PROGRAMS')
else:
    desktop_dir = get_folder_path('CSIDL_DESKTOPDIRECTORY')
    start_menu = get_folder_path('CSIDL_PROGRAMS')


def quoted(s):
    """
    quotes a string if necessary.
    """
    # strip any existing quotes
    s = s.strip(u'"')
    if u' ' in s or u'/' in s:
        return u'"%s"' % s
    else:
        return s


class Menu(object):
    def __init__(self, name):
        self.path = join(start_menu, name)

    def create(self):
        if not isdir(self.path):
            os.mkdir(self.path)

    def remove(self):
        rm_empty_dir(self.path)


class ShortCut(object):
    def __init__(self, menu, shortcut, prefix, env_name, env_setup_cmd):
        """
        Prefix is the system prefix to be used -- this is needed since
        there is the possibility of a different Python's packages being managed.
        """
        self.menu = menu
        self.shortcut = shortcut
        self.prefix = prefix
        self.env_name = env_name
        self.env_setup_cmd = env_setup_cmd

    def remove(self):
        self.create(remove=True)

    def create(self, remove=False):
        cmd = self.env_setup_cmd + " && " if self.env_setup_cmd else ""
        if "pywscript" in self.shortcut:
            cmd = cmd + join(self.prefix, 'pythonw.exe')
            args = self.shortcut["pywscript"].split()

        elif "pyscript" in self.shortcut:
            cmd = cmd + join(self.prefix, 'python.exe')
            args = self.shortcut["pyscript"].split()

        elif "webbrowser" in self.shortcut:
            cmd = cmd + join(self.prefix, 'pythonw.exe')
            args = ['-m', 'webbrowser', '-t', self.shortcut['webbrowser']]

        elif "script" in self.shortcut:
            cmd = cmd + join(self.prefix, self.shortcut["script"].replace('/', '\\'))
            args = [self.shortcut['scriptargument']]

        else:
            raise Exception("Nothing to do: %r" % self.shortcut)

        workdir = self.shortcut.get('workdir', '')
        icon = self.shortcut.get('icon', '')
        for a, b in [
            ('${PREFIX}', self.prefix),
            ('${PYTHON_SCRIPTS}', join(self.prefix, 'Scripts')),
            ('${MENU_DIR}', join(self.prefix, 'Menu')),
            ('${PERSONALDIR}', get_folder_path('CSIDL_PERSONAL')),
            ('${USERPROFILE}', get_folder_path('CSIDL_PROFILE')),
            ('${ENV_NAME}', self.env_name),
            ]:
            args = [s.replace(a, b) for s in args]
            workdir = workdir.replace(a, b)
            icon = icon.replace(a, b)
        # Fix up the '/' to '\'
        workdir = workdir.replace('/', '\\')
        icon = icon.replace('/', '\\')

        # Create the working directory if it doesn't exist
        if workdir:
            if not isdir(workdir):
                os.makedirs(workdir)
        else:
            workdir = expanduser('~')

        # Menu link
        dst_dirs = [self.menu.path]

        # Desktop link
        if self.shortcut.get('desktop'):
            dst_dirs.append(desktop_dir)

        # Quicklaunch link
        if self.shortcut.get('quicklaunch'):
            dst_dirs.append(quicklaunch_dir)

        name_suffix = " ({})".format(self.env_name) if self.env_name else ""
        for dst_dir in dst_dirs:
            dst = join(dst_dir, self.shortcut['name'] + name_suffix + '.lnk')
            if remove:
                rm_rf(dst)
            else:
                # The API for the call to 'create_shortcut' has 3
                # required arguments (path, description and filename)
                # and 4 optional ones (args, working_dir, icon_path and
                # icon_index).
                create_shortcut(
                    u'' + quoted(cmd),
                    u'' + self.shortcut['name'] + name_suffix,
                    u'' + dst,
                    u' '.join(quoted(arg) for arg in args),
                    u'' + workdir,
                    u'' + icon,
                )
