# Copyright (c) 2008-2011 by Enthought, Inc.
# Copyright (c) 2013 Continuum Analytics, Inc.
# All rights reserved.

from __future__ import absolute_import

from functools import partial
import os
from os.path import expanduser, isdir, join, exists
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


def substitute_env_variables(text, env_prefix=sys.prefix, env_name=None):
    # When conda is using Menuinst, only the root Conda installation ever calls menuinst.  Thus,
    #    these calls to sys refer to the root Conda installation, NOT the child environment
    py_major_ver = sys.version_info[0]
    py_bitness = 8 * tuple.__itemsize__

    for a, b in [
        ('${PREFIX}', env_prefix),
        ('${ROOT_PREFIX}', sys.prefix),
        ('${PYTHON_SCRIPTS}', join(env_prefix, 'Scripts')),
        ('${MENU_DIR}', join(env_prefix, 'Menu')),
        ('${PERSONALDIR}', get_folder_path('CSIDL_PERSONAL')),
        ('${USERPROFILE}', get_folder_path('CSIDL_PROFILE')),
        ('${ENV_NAME}', env_name if env_name else ""),
        ('${PY_VER}', str(py_major_ver)),
        ('${PLATFORM}', "(%s-bit)" % py_bitness),
        ]:
        text = text.replace(a, b)
    return text


class Menu(object):
    def __init__(self, name, prefix=sys.prefix):
        self.path = join(start_menu, substitute_env_variables(name))

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
        f.write('"{activate_script}" && "{other_cmd}" "{args}"\n"'.format(
                  activate_script=join(prefix, "Scripts", setup_cmd),
                  other_cmd=join(prefix, other_cmd),
                  args = '" "'.join(args)
                  )
                )
    return filename


class ShortCut(object):
    def __init__(self, menu, shortcut, target_prefix, env_name, env_setup_cmd):
        """
        Prefix is the system prefix to be used -- this is needed since
        there is the possibility of a different Python's packages being managed.
        """
        self.menu = menu
        self.shortcut = shortcut
        self.prefix = target_prefix
        self.env_name = env_name
        self.env_setup_cmd = env_setup_cmd

    def remove(self):
        self.create(remove=True)

    def create(self, remove=False):
        args = []
        bat_func = partial(write_bat_file, self.prefix, self.env_setup_cmd)
        if "pywscript" in self.shortcut:
            cmd = bat_func('pythonw.exe', self.shortcut["pywscript"].split())
        elif "pyscript" in self.shortcut:
            cmd = bat_func('python.exe', self.shortcut["pyscript"].split())
        elif "webbrowser" in self.shortcut:
            cmd = bat_func('pythonw.exe', ['-m', 'webbrowser', '-t',
                                               self.shortcut['webbrowser']])
        elif "script" in self.shortcut:
            cmd = bat_func(join(self.prefix, self.shortcut["script"].replace('/', '\\')),
                               self.shortcut["pyscript"].split())

        elif "system" in self.shortcut:
            cmd = substitute_env_variables(self.shortcut["system"],
                                             env_prefix=self.prefix,
                                             env_name=self.env_name).replace('/', '\\')
            args = self.shortcut['scriptargument']

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
