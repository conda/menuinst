# Copyright (c) 2008-2011 by Enthought, Inc.
# All rights reserved.

import os
import sys
from os.path import isdir, join

from utils import rm_empty_dir, rm_rf

import wininst


try:
    from custom_tools.msi_property import get
    mode = ('user', 'system')[get('ALLUSERS') == '1']
    addtodesktop = bool(get('ADDTODESKTOP') == '1')
    addtolauncher = bool(get('ADDTOLAUNCHER') == '1')
except ImportError:
    mode = 'user'
    addtodesktop = True
    addtolauncher = True


quicklaunch_dir = join(wininst.get_special_folder_path('CSIDL_APPDATA'),
                       "Microsoft", "Internet Explorer", "Quick Launch")

if mode == 'system':
    desktop_dir = wininst.get_special_folder_path(
                                           'CSIDL_COMMON_DESKTOPDIRECTORY')
    start_menu = wininst.get_special_folder_path('CSIDL_COMMON_PROGRAMS')
else:
    desktop_dir = wininst.get_special_folder_path('CSIDL_DESKTOPDIRECTORY')
    start_menu = wininst.get_special_folder_path('CSIDL_PROGRAMS')


def quoted(s):
    """
    quotes a string if necessary.
    """
    # strip any existing quotes
    s = s.strip('"')
    if ' ' in s:
        return '"%s"' % s
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

    def __init__(self, menu, shortcut, prefix=None):
        """
        Prefix is the system prefix to be used -- this is needed since
        there is the possibility of a different Python's packages being managed.
        """
        self.menu = menu
        self.shortcut = shortcut
        self.prefix = prefix if prefix is not None else sys.prefix
        self.cmd = shortcut['cmd']

    def remove(self):
        self.create(remove=True)

    def create(self, remove=False):
        # Separate the arguments to the invoked command from the command
        # itself.
        cmd = self.cmd[0]
        args = self.cmd[1:]
        executable = join(self.prefix, 'python.exe')

        # Handle the special '{{FILEBROWSER}}' command by using webbrowser
        # since using just the path name pops up a dialog asking for which
        # application to use.  Using 'explorer.exe' picks up
        # c:/windows/system32/explorer.exe which does not work.  Webbrowser
        # does the right thing.
        if cmd == '{{FILEBROWSER}}':
            cmd = executable
            args = ['-m', 'webbrowser'] + args

        # Otherwise, handle the special '{{WEBBROWSER}}' command by
        # invoking the Python standard lib's 'webbrowser' script.  This
        # allows us to specify that the url(s) should be opened in new
        # tabs.
        #
        # If this doesn't work, see the following website for details of
        # the special URL shortcut file format.  While split across two
        # lines it is one URL:
        #   http://delphi.about.com/gi/dynamic/offsite.htm?site= \
        #        http://www.cyanwerks.com/file-format-url.html
        elif cmd == '{{WEBBROWSER}}':
            cmd = executable
            args = ['-m', 'webbrowser', '-t'] + args

        # The API for the call to 'wininst.create_shortcut' has 3 required
        # arguments:-
        #
        # path, description and filename
        #
        # and 4 optional arguments:-
        #
        # args, working_dir, icon_path and icon_index
        #
        # We always pass the args argument, but we only pass the working
        # directory and the icon path if given, and we never currently pass the
        # icon index.
        working_dir = quoted(self.shortcut.get('working_dir', ''))
        icon        = self.shortcut.get('icon')
        if working_dir and icon:
            shortcut_args = [working_dir, icon]

        elif working_dir and not icon:
            shortcut_args = [working_dir]

        elif not working_dir and icon:
            shortcut_args = ['', icon]

        else:
            shortcut_args = []

        # Menu link
        dst_dirs = [self.menu.path]

        # Desktop link
        if self.shortcut.get('desktop') and addtodesktop:
            dst_dirs.append(desktop_dir)

        # Quicklaunch link
        if self.shortcut.get('quicklaunch') and addtolauncher:
            dst_dirs.append(quicklaunch_dir)

        for dst_dir in dst_dirs:
            dst = join(dst_dir, self.shortcut['name'] + '.lnk')
            if remove:
                rm_rf(dst)
            else:
                wininst.create_shortcut(
                    quoted(cmd),
                    self.shortcut['comment'],
                    dst,
                    ' '.join(quoted(arg) for arg in args),
                    *shortcut_args)
