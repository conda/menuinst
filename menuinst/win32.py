# Copyright (c) 2008-2011 by Enthought, Inc.
# Copyright (c) 2013 Continuum Analytics, Inc.
# All rights reserved.

from __future__ import absolute_import

from functools import partial
import os
from os.path import expanduser, isdir, join, exists
import platform
import subprocess
import sys

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


def substitute_env_variables(text, root_prefix=sys.prefix, env_prefix=sys.prefix, env_name=None):
    # these subprocesses are a little hairy, but required to have the menu
    #   entry reflect the ROOT conda installation, not our environment.
    py_ver_subprocess = subprocess.Popen([join(root_prefix, "python"), "-c",
                                          "import sys; print(sys.version_info.major)"],
                                         stdout=subprocess.PIPE, shell=True)
    py_major_ver = py_ver_subprocess.stdout.readline().strip()
    if sys.version_info.major >= 3:
        py_major_ver = str(py_major_ver, encoding="utf-8")
    py_bitness_subprocess = subprocess.Popen([join(root_prefix, "python"), "-c",
                                              "print(tuple.__itemsize__)"],
                                             stdout=subprocess.PIPE, shell=True)
    py_bitness = py_bitness_subprocess.stdout.readline().strip()
    if sys.version_info.major >= 3:
        py_bitness = str(py_bitness, encoding="utf-8")
    py_bitness = 8 * int(py_bitness)

    for a, b in [
        ('${PREFIX}', env_prefix),
        ('${ROOT_PREFIX}', root_prefix),
        ('${PYTHON_SCRIPTS}', join(env_prefix, 'Scripts')),
        ('${MENU_DIR}', join(env_prefix, 'Menu')),
        ('${PERSONALDIR}', get_folder_path('CSIDL_PERSONAL')),
        ('${USERPROFILE}', get_folder_path('CSIDL_PROFILE')),
        ('${ENV_NAME}', env_name if env_name else ""),
        ('${PY_VER}', py_major_ver),
        ('${PLATFORM}', "%s-bit" % py_bitness),
        ]:
        text = text.replace(a, b)
    return text


class Menu(object):
    def __init__(self, name, prefix=sys.prefix):
        self.path = join(start_menu, substitute_env_variables(name, root_prefix=prefix))

    def create(self):
        if not isdir(self.path):
            os.mkdir(self.path)

    def remove(self):
        rm_empty_dir(self.path)


def write_bat_file(prefix, setup_cmd, other_cmd, args):
    args = [substitute_env_variables(arg, env_prefix=prefix) for arg in args]
    args[0] = args[0].replace("/", "\\")
    scriptname = os.path.split(args[0])[1]
    filename = join(prefix, "Scripts\\launch_{}_{}.bat".format(other_cmd, scriptname))
    with open(filename, "w") as f:
        f.write(setup_cmd+" && ")
        f.write(join(prefix, other_cmd) + " " + " ".join(args) + "\n")
    return filename


class ShortCut(object):
    def __init__(self, menu, shortcut, root_prefix, target_prefix, env_name, env_setup_cmd):
        """
        Prefix is the system prefix to be used -- this is needed since
        there is the possibility of a different Python's packages being managed.
        """
        self.menu = menu
        self.shortcut = shortcut
        self.prefix = target_prefix
        self.root_prefix = root_prefix
        self.env_name = env_name
        self.env_setup_cmd = env_setup_cmd

    def remove(self):
        self.create(remove=True)

    def create(self, remove=False):
        args = []
        bat_func = partial(write_bat_file, self.prefix, self.env_setup_cmd)
        if "pywscript" in self.shortcut:
            if self.env_setup_cmd:
                cmd = bat_func('pythonw.exe', self.shortcut["pywscript"].split())
            else:
                cmd = join(self.prefix, 'pythonw.exe')
                args = self.shortcut["pywscript"].split()

        elif "pyscript" in self.shortcut:
            if self.env_setup_cmd:
                cmd = bat_func('python.exe', self.shortcut["pyscript"].split())
            else:
                cmd = join(self.prefix, 'python.exe')
                args = self.shortcut["pyscript"].split()

        elif "webbrowser" in self.shortcut:
            if self.env_setup_cmd:
                cmd = bat_func('pythonw.exe', ['-m', 'webbrowser', '-t',
                                               self.shortcut['webbrowser']])
            else:
                cmd = join(self.prefix, 'pythonw.exe')
                args = ['-m', 'webbrowser', '-t', self.shortcut['webbrowser']]

        elif "script" in self.shortcut:
            if self.env_setup_cmd:
                cmd = bat_func(join(self.prefix, self.shortcut["script"].replace('/', '\\')),
                               self.shortcut["pyscript"].split())
            else:
                cmd = join(self.prefix, self.shortcut["script"].replace('/', '\\'))
                args = self.shortcut['scriptargument']

        elif "system" in self.shortcut:
            cmd = self.shortcut["system"].replace('/', '\\')
            args = self.shortcut['scriptargument']
            args = [substitute_env_variables(s, root_prefix=self.root_prefix,
                                             env_prefix=self.prefix,
                                             env_name=self.env_name) for s in args]

        else:
            raise Exception("Nothing to do: %r" % self.shortcut)

        workdir = self.shortcut.get('workdir', '')
        icon = self.shortcut.get('icon', '')

        args = [substitute_env_variables(s, env_prefix=self.prefix, env_name=self.env_name) for s in args]
        workdir = substitute_env_variables(workdir, env_prefix=self.prefix, env_name=self.env_name)
        icon = substitute_env_variables(icon, env_prefix=self.prefix, env_name=self.env_name)

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
