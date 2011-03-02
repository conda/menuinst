# Copyright (c) 2008-2011 by Enthought, Inc.
# All rights reserved.

import os
from os.path import exists, isdir, isfile, islink, join

from egginst.utils import rm_empty_dir, rm_rf

from osx_application import Application



class Menu(object):

    def __init__(self, name):
        self.path = join('/Applications', name)

    def create(self):
        if not isdir(self.path):
            os.mkdir(self.path)

    def remove(self):
        rm_empty_dir(self.path)

    def add_shortcut(self, shortcut):
        # Separate the arguments to the invoked command from the command
        # itself.   Note that since Finder is automatically launched
        # when a folder link is selected, and that the default web
        # browser is launched when a html-like file link is selected,
        # we can simply strip-out and ignore the special {{FILEBROWSER}}
        # and {{WEBBROWSER}} placeholders.
        #
        # FIXME: Should we instead use Python standard lib's default
        # webbrowser.py script to open a browser?  We then get to
        # control whether it opens in a new tab or not.  See the win32
        # platform support for an example.
        args = []
        cmd = shortcut['cmd']
        if cmd[0] in ('{{FILEBROWSER}}', '{{WEBBROWSER}}'):
            del cmd[0]
        if len(cmd) > 1:
            args = cmd[1:]
        cmd = cmd[0]

        # If the command is a path to an executable file, create a
        # double-clickable shortcut that will execute it.
        if isfile(cmd) and os.access(cmd, os.X_OK):
            shortcut['args'] = [cmd] + args
            shortcut['menu_dir'] = self.path
            Application(shortcut).create()

        # Otherwise, just create a symlink to the specified command
        # value.  Note that it is possible we may only need this logic
        # as symlinks to executable scripts are double-clickable on
        # OS X 10.5 (though there would be no way to apply custom icons
        # then.)
        else:
            name = shortcut['name']
            path = join(self.path, name)

            # Remove the symlink if it exists already, we always want to be
            # able to reinstall
            if islink(path):
                print "Warning: link %r already exists, unlinking" % path
                os.remove(path)

            # If there was a link it's removed now, but maybe there is still
            # a file or directory
            if exists(path):
                print "Error: %r exists, can't create link" % path
            else:
                os.symlink(cmd, path)
