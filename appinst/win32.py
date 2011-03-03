# Copyright (c) 2008-2011 by Enthought, Inc.
# All rights reserved.

import os
import sys
from os.path import isdir, join

from egginst.utils import rm_empty_dir, rm_rf

import wininst
import win32_common as common


try:
    from custom_tools.msi_property import get
    mode = ('user', 'system')[get('ALLUSERS') == '1']
    addtodesktop = bool(get('ADDTODESKTOP') == '1')
    addtolauncher = bool(get('ADDTOLAUNCHER') == '1')
except ImportError:
    mode = 'user'
    addtodesktop = True
    addtolauncher = True


desktop_dir = common.get_desktop_directory()
quicklaunch_dir = common.get_quick_launch_directory()

if mode == 'system':
    start_menu = common.get_all_users_programs_start_menu()
else:
    start_menu = common.get_current_user_programs_start_menu()


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

    def __init__(self, menu, shortcut):
        self.menu = menu
        self.shortcut = shortcut
        self.cmd = shortcut['cmd']

    def remove(self):
        self.create(remove=True)

    def create(self, remove=False):
        # Separate the arguments to the invoked command from the command
        # itself.
        cmd = self.cmd[0]
        args = self.cmd[1:]

        # Handle the special '{{FILEBROWSER}}' command by stripping it
        # out since File Explorer will automatically be launched when a
        # folder link is separated.
        if cmd == '{{FILEBROWSER}}':
            cmd = args[0]
            args = args[1:]

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
            import webbrowser
            cmd = join(sys.prefix, 'python.exe')
            args = [webbrowser.__file__, '-t'] + args

        # Now create the actual Windows shortcut.  Note that the API to
        # create a windows shortcut requires that a path to the icon
        # file be in a weird place -- second in a variable length
        # list of args.
        icon = self.shortcut.get('icon')
        if icon:
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
                    self.comment,
                    dst,
                    ' '.join(quoted(arg) for arg in args),
                    *shortcut_args)
