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

dirs = {"system": {"desktop": get_folder_path('CSIDL_COMMON_DESKTOPDIRECTORY'),
                   "start": get_folder_path('CSIDL_COMMON_PROGRAMS'),
                   "quicklaunch": join(get_folder_path('CSIDL_COMMON_APPDATA'), *quicklaunch_dirs),
                   "documents": get_folder_path('CSIDL_COMMON_DOCUMENTS'),
                   "profile": get_folder_path('CSIDL_PROFILE')}}
try:
    dirs["user"] = {"desktop": get_folder_path('CSIDL_DESKTOPDIRECTORY'),
                    "start": get_folder_path('CSIDL_PROGRAMS'),
                    # LOCAL_APPDATA because that is what the NSIS installer uses
                    # 'as this is the only place guaranteed to not be backed by a network share
                    #  or included in a user's roaming profile'
                    "quicklaunch": join(get_folder_path('CSIDL_LOCAL_APPDATA'), *quicklaunch_dirs),
                    "documents": get_folder_path('CSIDL_PERSONAL'),
                    "profile": get_folder_path('CSIDL_PROFILE')}
except:
    pass

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


def substitute_env_variables(text, dir):
    # When conda is using Menuinst, only the root Conda installation ever
    # calls menuinst.  Thus, these calls to sys refer to the root Conda
    # installation, NOT the child environment
    py_major_ver = sys.version_info[0]
    py_bitness = 8 * tuple.__itemsize__

    env_prefix = to_unicode(dir['prefix'])
    text = to_unicode(text)
    env_name = to_unicode(dir['env_name'])

    for a, b in (
        (u'${PREFIX}', env_prefix),
        (u'${ROOT_PREFIX}', unicode_prefix),
        (u'${PYTHON_SCRIPTS}',
          os.path.normpath(join(env_prefix, u'Scripts')).replace(u"\\", u"/")),
        (u'${MENU_DIR}', join(env_prefix, u'Menu')),
        (u'${PERSONALDIR}', dir['documents']),
        (u'${USERPROFILE}', dir['profile']),
        (u'${ENV_NAME}', env_name),
        (u'${PY_VER}', u'%d' % (py_major_ver)),
        (u'${PLATFORM}', u"(%s-bit)" % py_bitness),
        ):
        if b:
            text = text.replace(a, b)
    return text


class Menu(object):
    def __init__(self, name, prefix=unicode_prefix, env_name=u"", mode=None):
        """
        Prefix is the system prefix to be used -- this is needed since
        there is the possibility of a different Python's packages being managed.
        """

        # bytestrings passed in need to become unicode
        self.prefix = to_unicode(prefix)
        if 'user' in dirs:
            used_mode = mode if mode else ('user' if exists(join(prefix, u'.nonadmin')) else 'system')
        else:
            used_mode = 'system'
        try:
            self.set_dir(name, prefix, env_name, used_mode)
        except WindowsError:
            # We get here if we aren't elevated.  This is different from
            #   permissions: a user can have permission, but elevation is still
            #   required.  If the process isn't elevated, we get the
            #   WindowsError
            if 'user' in dirs:
                logging.warn("Insufficient permissions to write menu folder.  "
                             "Falling back to user location")
                try:
                    self.set_dir(name, prefix, env_name, 'user')
                except:
                    pass
            else:
                logging.fatal("Unable to create AllUsers menu folder")

    def set_dir(self, name, prefix, env_name, mode):
        self.mode = mode
        self.dir = dirs[mode]
        self.dir['prefix'] = prefix
        self.dir['env_name'] = env_name
        folder_name = substitute_env_variables(name, self.dir)
        self.path = join(self.dir["start"], folder_name)
        self.create()

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
    def __init__(self, menu, shortcut):
        self.menu = menu
        self.shortcut = shortcut

    def remove(self):
        self.create(remove=True)

    def create(self, remove=False):
        args = []
        if "pywscript" in self.shortcut:
            cmd = join(self.menu.prefix, u"pythonw.exe").replace("\\", "/")
            args = self.shortcut["pywscript"].split()
            args = get_python_args_for_subprocess(self.menu.prefix, args, cmd)
        elif "pyscript" in self.shortcut:
            cmd = join(self.menu.prefix, u"python.exe").replace("\\", "/")
            args = self.shortcut["pyscript"].split()
            args = get_python_args_for_subprocess(self.menu.prefix, args, cmd)
        elif "webbrowser" in self.shortcut:
            cmd = join(unicode_prefix, u'pythonw.exe')
            args = ['-m', 'webbrowser', '-t', self.shortcut['webbrowser']]
        elif "script" in self.shortcut:
            cmd = self.shortcut["script"].replace('/', '\\')
            extend_script_args(args, self.shortcut)
            args = get_python_args_for_subprocess(self.menu.prefix, args, cmd)
            cmd = join(unicode_prefix, u"pythonw.exe").replace("\\", "/")
        elif "system" in self.shortcut:
            cmd = substitute_env_variables(
                     self.shortcut["system"],
                     self.menu.dir).replace('/', '\\')
            extend_script_args(args, self.shortcut)
        else:
            raise Exception("Nothing to do: %r" % self.shortcut)

        workdir = self.shortcut.get('workdir', '')
        icon = self.shortcut.get('icon', '')

        args = [substitute_env_variables(s, self.menu.dir) for s in args]
        workdir = substitute_env_variables(workdir, self.menu.dir)
        icon = substitute_env_variables(icon, self.menu.dir)

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
            dst_dirs.append(self.menu.dir['desktop'])

        # Quicklaunch link
        if self.shortcut.get('quicklaunch'):
            dst_dirs.append(self.menu.dir['quicklaunch'])

        name_suffix = " ({})".format(self.menu.dir['env_name']) if self.menu.dir['env_name'] else ""
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
