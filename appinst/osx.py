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
        

class ShortCut(object):

    def __init__(self, menu, shortcut):
        self.menu = menu
        self.shortcut = shortcut
        for var_name in ('name', 'cmd'):
            if var_name in shortcut:
                setattr(self, var_name, shortcut[var_name])

        if isfile(self.cmd[0]) and os.access(self.cmd[0], os.X_OK):
            self.tp = 'app'
            self.path = join(menu.path, self.name + '.app')
        else:
            self.tp = 'link'
            self.path = join(menu.path, self.name)

    def remove(self):
        rm_rf(self.path)

    def create(self):
        if self.tp == 'app':
            self.shortcut['args'] = self.cmd
            self.shortcut['menu_dir'] = self.menu.path
            Application(self.shortcut).create()

        elif self.tp == 'link':
            src = self.cmd[0]
            if src.startswith('{{'):
                src = self.cmd[1]

            rm_rf(self.path)
            os.symlink(src, self.path)
