# Copyright (c) 2008-2011 by Enthought, Inc.
# Copyright (c) 2013-2015 Continuum Analytics, Inc.
# All rights reserved.

from __future__ import absolute_import, unicode_literals

import logging
import os
import sys
from os.path import expanduser, isdir, join, exists

from .utils import rm_empty_dir, rm_rf
import platform
if platform.release() == "XP":
    from .csidl import get_folder_path
    # CSIDL does not provide a direct path to Quick launch.  Start with APPDATA path, go from there.
    quicklaunch_dirs = ["Microsoft", "Internet Explorer", "Quick Launch"]
else:
    from .knownpaths import get_folder_path
    # KNOWNFOLDERID does provide a direct path to Quick luanch.  No additional path necessary.
    quicklaunch_dirs = []
from .winshortcut import create_shortcut

quicklaunch_dir = join(get_folder_path('CSIDL_APPDATA'), *quicklaunch_dirs)

dirs = {"system": {"desktop": get_folder_path('CSIDL_COMMON_DESKTOPDIRECTORY'),
                   "start": get_folder_path('CSIDL_COMMON_PROGRAMS')},
        "user": {"desktop": get_folder_path('CSIDL_DESKTOPDIRECTORY'),
                 "start": get_folder_path('CSIDL_PROGRAMS')}}

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


def to_unicode(var, codec=sys.getdefaultencoding()):
    if not codec:
        codec="utf-8"
    if hasattr(var, "decode"):
        var = var.decode(codec)
    return var


def to_bytes(var, codec=sys.getdefaultencoding()):
    if not codec:
        codec="utf-8"
    if hasattr(var, "encode"):
        var = var.encode(codec)
    return var


unicode_prefix = to_unicode(sys.prefix)


def substitute_env_variables(text, env_prefix=unicode_prefix, env_name=None):
    # When conda is using Menuinst, only the root Conda installation ever
    # calls menuinst.  Thus, these calls to sys refer to the root Conda
    # installation, NOT the child environment
    py_major_ver = sys.version_info[0]
    py_bitness = 8 * tuple.__itemsize__

    env_prefix = to_unicode(env_prefix)
    text = to_unicode(text)
    env_name = to_unicode(env_name)

    for a, b in [
        (u'${PREFIX}', env_prefix),
        (u'${ROOT_PREFIX}', unicode_prefix),
        (u'${PYTHON_SCRIPTS}',
          os.path.normpath(join(env_prefix, u'Scripts')).replace(u"\\", u"/")),
        (u'${MENU_DIR}', join(env_prefix, u'Menu')),
        (u'${PERSONALDIR}', get_folder_path('CSIDL_PERSONAL')),
        (u'${USERPROFILE}', get_folder_path('CSIDL_PROFILE')),
        (u'${ENV_NAME}', env_name if env_name else u""),
        (u'${PY_VER}', u'%d' % (py_major_ver)),
        (u'${PLATFORM}', u"(%s-bit)" % py_bitness),
        ]:
        text = text.replace(a, b)
    return text


class Menu(object):
    def __init__(self, name, prefix=unicode_prefix, mode=None):
        # bytestrings passed in need to become unicode
        prefix = to_unicode(prefix)
        self.mode = mode if mode else ('user' if exists(join(prefix, u'.nonadmin')) else 'system')
        folder_name = substitute_env_variables(name)
        self.path = join(dirs[self.mode]["start"], folder_name)
        try:
            self.create()
        except WindowsError:
            # We get here if we aren't elevated.  This is different from
            #   permissions: a user can have permission, but elevation is still
            #   required.  If the process isn't elevated, we get the
            #   WindowsError
            logging.warn("Insufficient permissions to write menu folder.  "
                         "Falling back to user location")
            self.path = join(dirs["user"]["start"], folder_name)
            self.mode = "user"

    def create(self):
        if not isdir(self.path):
            os.mkdir(self.path)

    def remove(self):
        rm_empty_dir(self.path)


def get_python_args_for_subprocess(prefix, args, cmd):
    return [quoted(join(unicode_prefix, u'cwp.py')), quoted(prefix),
            quoted(cmd)] + args


def extend_script_args(args, shortcut):
    try:
        args.append(shortcut['scriptargument'])
    except KeyError:
        pass
    try:
        args.extend(shortcut['scriptarguments'])
    except KeyError:
        pass


class ShortCut(object):
    def __init__(self, menu, shortcut, target_prefix, env_name):
        """
        Prefix is the system prefix to be used -- this is needed since
        there is the possibility of a different Python's packages being managed.
        """
        self.menu = menu
        self.shortcut = shortcut
        self.prefix = to_unicode(target_prefix)
        self.env_name = env_name

    def remove(self):
        self.create(remove=True)

    def create(self, remove=False):
        args = []
        if "pywscript" in self.shortcut:
            cmd = join(self.prefix, u"pythonw.exe").replace("\\", "/")
            args = self.shortcut["pywscript"].split()
            args = get_python_args_for_subprocess(self.prefix, args, cmd)
        elif "pyscript" in self.shortcut:
            cmd = join(self.prefix, u"python.exe").replace("\\", "/")
            args = self.shortcut["pyscript"].split()
            args = get_python_args_for_subprocess(self.prefix, args, cmd)
        elif "webbrowser" in self.shortcut:
            cmd = join(unicode_prefix, u'pythonw.exe')
            args = ['-m', 'webbrowser', '-t', self.shortcut['webbrowser']]
        elif "script" in self.shortcut:
            cmd = self.shortcut["script"].replace('/', '\\')
            extend_script_args(args, self.shortcut)
            args = get_python_args_for_subprocess(self.prefix, args, cmd)
            cmd = join(unicode_prefix, u"pythonw.exe").replace("\\", "/")
        elif "system" in self.shortcut:
            cmd = substitute_env_variables(
                     self.shortcut["system"],
                     env_prefix=self.prefix,
                     env_name=self.env_name).replace('/', '\\')
            extend_script_args(args, self.shortcut)
        else:
            raise Exception("Nothing to do: %r" % self.shortcut)

        workdir = self.shortcut.get('workdir', '')
        icon = self.shortcut.get('icon', '')

        args = [substitute_env_variables(s, env_prefix=self.prefix,
                                         env_name=self.env_name) for s in args]
        workdir = substitute_env_variables(workdir,
                                           env_prefix=self.prefix,
                                           env_name=self.env_name)
        icon = substitute_env_variables(icon, env_prefix=self.prefix,
                                        env_name=self.env_name)

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
            dst_dirs.append(dirs[self.menu.mode]['desktop'])

        # Quicklaunch link
        if self.shortcut.get('quicklaunch'):
            dst_dirs.append(dirs[self.menu.mode]['quicklaunch'])

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
