# Copyright (c) 2008-2011 by Enthought, Inc.
# Copyright (c) 2013-2017 Continuum Analytics, Inc.
# All rights reserved.

from __future__ import absolute_import, unicode_literals

import ctypes
import logging
import os
from os.path import expanduser, isdir, join, exists
import pywintypes
import sys
import locale


from .utils import rm_empty_dir, rm_rf
from .knownfolders import get_folder_path, FOLDERID
# KNOWNFOLDERID does provide a direct path to Quick Launch.  No additional path necessary.
from .winshortcut import create_shortcut


# This allows debugging installer issues using DebugView from Microsoft.
OutputDebugString = ctypes.windll.kernel32.OutputDebugStringW
OutputDebugString.argtypes = [ctypes.c_wchar_p]


class DbgViewHandler(logging.Handler):
    def emit(self, record):
        OutputDebugString(self.format(record))


logger = logging.getLogger("menuinst_win32")
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)
dbgview = DbgViewHandler()
dbgview.setLevel(logging.DEBUG)
logger.addHandler(dbgview)
logger.addHandler(stream_handler)

# When running as 'nt authority/system' as sometimes people do via SCCM,
# various folders do not exist, such as QuickLaunch. This doesn't matter
# as we'll use the "system" key finally and check for the "quicklaunch"
# subkey before adding any Quick Launch menu items.

# It can happen that some of the dirs[] entires refer to folders that do not
# exist, in which case, the 2nd entry of the value tuple is a sub-class of
# Exception.

dirs_src = {"system": {  "desktop": get_folder_path(FOLDERID.PublicDesktop),
                           "start": get_folder_path(FOLDERID.CommonPrograms),
                       "documents": get_folder_path(FOLDERID.PublicDocuments),
                         "profile": get_folder_path(FOLDERID.Profile)},

            "user": {    "desktop": get_folder_path(FOLDERID.Desktop),
                           "start": get_folder_path(FOLDERID.Programs),
                     "quicklaunch": get_folder_path(FOLDERID.QuickLaunch),
                       "documents": get_folder_path(FOLDERID.Documents),
                         "profile": get_folder_path(FOLDERID.Profile)}}


def folder_path(preferred_mode, check_other_mode, key):
    ''' This function implements all heuristics and workarounds for messed up
        KNOWNFOLDERID registry values. It's also verbose (OutputDebugStringW)
        about whether fallbacks worked or whether they would have worked if
        check_other_mode had been allowed.
    '''
    other_mode = 'system' if preferred_mode == 'user' else 'user'
    path, exception = dirs_src[preferred_mode][key]
    if not exception:
        return path
    logger.info("WARNING: menuinst key: '%s'\n"
                "                 path: '%s'\n"
                "     .. excepted with: '%s' in knownfolders.py, implementing workarounds .."
                % (key, path, type(exception).__name__))
    # Since I have seen 'user', 'documents' set as '\\vmware-host\Shared Folders\Documents'
    # when there's no such server, we check 'user', 'profile' + '\Documents' before maybe
    # trying the other_mode (though I have chickened out on that idea).
    if preferred_mode == 'user' and key == 'documents':
        user_profile, exception = dirs_src['user']['profile']
        if not exception:
            path = join(user_profile, 'Documents')
            if os.access(path, os.W_OK):
                logger.info("  .. worked-around to: '%s'" % (path))
                return path
    path, exception = dirs_src[other_mode][key]
    # Do not fall back to something we cannot write to.
    if exception:
        if check_other_mode:
            logger.info("     .. despite 'check_other_mode'\n"
                        "        and 'other_mode' 'path' of '%s'\n"
                        "        it excepted with: '%s' in knownfolders.py" % (path,
                                                                    type(exception).__name__))
        else:
            logger.info("     .. 'check_other_mode' is False,\n"
                        "        and 'other_mode' 'path' is '%s'\n"
                        "        but it excepted anyway with: '%s' in knownfolders.py" % (path, type(exception).__name__))
        return None
    if not check_other_mode:
        logger.info("     .. due to lack of 'check_other_mode' not picking\n"
                    "        non-excepting path of '%s'\n in knownfolders.py" % (path))
        return None
    return path


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


def to_unicode(var, codec=locale.getpreferredencoding()):
    if sys.version_info[0] < 3 and isinstance(var, unicode):
        return var
    if not codec:
        codec="utf-8"
    if hasattr(var, "decode"):
        var = var.decode(codec)
    return var


def to_bytes(var, codec=locale.getpreferredencoding()):
    if isinstance(var, bytes):
        return var
    if not codec:
        codec="utf-8"
    if hasattr(var, "encode"):
        var = var.encode(codec)
    return var


if u'\\envs\\' in to_unicode(sys.prefix):
    logger.warn('menuinst called from non-root env %s' % (sys.prefix))
unicode_root_prefix = to_unicode(sys.prefix)


def substitute_env_variables(text, dir):
    # When conda is using Menuinst, only the root conda installation ever
    # calls menuinst.  Thus, these calls to sys refer to the root conda
    # installation, NOT the child environment
    py_major_ver = sys.version_info[0]
    py_bitness = 8 * tuple.__itemsize__

    env_prefix = to_unicode(dir['prefix'])
    text = to_unicode(text)
    env_name = to_unicode(dir['env_name'])

    for a, b in (
        (u'${PREFIX}', env_prefix),
        (u'${ROOT_PREFIX}', unicode_root_prefix),
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
    def __init__(self, name, prefix=unicode_root_prefix, env_name=u"", mode=None):
        """
        Prefix is the system prefix to be used -- this is needed since
        there is the possibility of a different Python's packages being managed.
        """

        # bytestrings passed in need to become unicode
        self.prefix = to_unicode(prefix)
        if 'user' in dirs_src:
            used_mode = mode if mode else ('user' if exists(join(self.prefix, u'.nonadmin')) else 'system')
        else:
            used_mode = 'system'
        logger.debug("Menu: name: '%s', prefix: '%s', env_name: '%s', mode: '%s', used_mode: '%s'"
                    % (name, self.prefix, env_name, mode, used_mode))
        try:
            self.set_dir(name, self.prefix, env_name, used_mode)
        except (WindowsError, pywintypes.error):
            # We get here if we aren't elevated.  This is different from
            #   permissions: a user can have permission, but elevation is still
            #   required.  If the process isn't elevated, we get the
            #   WindowsError
            if 'user' in dirs_src and used_mode == 'system':
                logger.warn("Insufficient permissions to write menu folder.  "
                            "Falling back to user location")
                try:
                    self.set_dir(name, self.prefix, env_name, 'user')
                except:
                    pass
            else:
                logger.fatal("Unable to create AllUsers menu folder")

    def set_dir(self, name, prefix, env_name, mode):
        self.mode = mode
        self.dir = dict()
        # I have chickened out on allowing check_other_mode. Really there needs
        # to be 3 distinct cases that 'menuinst' cares about:
        # priv-user doing system install
        # priv-user doing user-only install
        # non-priv-user doing user-only install
        # (priv-user only exists in an AllUsers installation).
        check_other_mode = False
        for k, v in dirs_src[mode].items():
            # We may want to cache self.dir to some files, one for AllUsers
            # (system) installs and one for each subsequent user install?
            self.dir[k] = folder_path(mode, check_other_mode, k)
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
    if "CMD.EXE" or "%COMSPEC%" in upper(cmd) and any(' ' in arg for arg in args):
        # cmd.exe expects a single string argument and requires
        # doubled-up quotes when any sub-arguments have spaces.
        # https://stackoverflow.com/a/6378038/3257826
        args=[quoted(" ".join(quoted(arg) for arg in args))]
    return [quoted(join(unicode_root_prefix, u'cwp.py')), quoted(prefix),
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
        # cmd is our root installation interpreter
        cmd = join(unicode_root_prefix, u"pythonw.exe").replace("\\", "/")
        # each of these roll the subprocess cmd into args
        if "pywscript" in self.shortcut:
            subprocess_cmd = join(self.menu.prefix, u"pythonw.exe").replace("\\", "/")
            args = self.shortcut["pywscript"].split()
            args = get_python_args_for_subprocess(self.menu.prefix, args, subprocess_cmd)
        elif "pyscript" in self.shortcut:
            subprocess_cmd = join(self.menu.prefix, u"python.exe").replace("\\", "/")
            args = self.shortcut["pyscript"].split()
            args = get_python_args_for_subprocess(self.menu.prefix, args, subprocess_cmd)
        elif "webbrowser" in self.shortcut:
            args = ['-m', 'webbrowser', '-t', self.shortcut['webbrowser']]
        elif "script" in self.shortcut:
            subprocess_cmd = join(unicode_root_prefix, u"pythonw.exe").replace("\\", "/")
            args.append(self.shortcut["script"].replace('/', '\\'))
            extend_script_args(args, self.shortcut)
            args = get_python_args_for_subprocess(self.menu.prefix, args, subprocess_cmd)
        elif "system" in self.shortcut:
            subprocess_cmd = substitute_env_variables(self.shortcut["system"],
                                                      self.menu.dir).replace('/', '\\')
            args = get_python_args_for_subprocess(self.menu.prefix, args, subprocess_cmd)
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
        if self.shortcut.get('quicklaunch') and 'quicklaunch' in self.menu.dir:
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
