# Copyright (c) 2008-2011 by Enthought, Inc.
# All rights reserved.

import re
import os
import shutil
import sys
import time
import xml.etree.ElementTree as ET
from os.path import (abspath, basename, dirname, exists, expanduser,
                     isdir, isfile, join)

from egginst.utils import rm_rf

from freedesktop import make_desktop_entry, make_directory_entry


# datadir: the directory that should contain the desktop and directory entries
# sysconfdir: the directory that should contain the XML menu files
if os.getuid() == 0:
    mode = 'system'
    datadir = '/usr/share'
    sysconfdir = '/etc/xdg'
else:
    mode = 'user'
    datadir = os.environ.get('XDG_DATA_HOME',
                             abspath(expanduser('~/.local/share')))
    sysconfdir = os.environ.get('XDG_CONFIG_HOME',
                                abspath(expanduser('~/.config')))




def indent(elem, level=0):
    "Adds whitespace to the tree, so that it results in a pretty printed tree."
    XMLindentation = "    "
    i = "\n" + level * XMLindentation
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + XMLindentation
        for e in elem:
            indent(e, level+1)
            if not e.tail or not e.tail.strip():
                e.tail = i + XMLindentation
        if not e.tail or not e.tail.strip():
            e.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def ensure_child_element(parent_element, tag, text=None):
    """
    Ensure there is a sub-element of the specified tag type.
    The sub-element is given the specified text content if text is not None.
    The sub-element is returned.
    """
    # Ensure the element exists.
    element = parent_element.find(tag)
    if element is None:
        element = ET.SubElement(parent_element, tag)

    # If specified, set its text
    if text is not None:
        element.text = text

    return element


class Menu(object):

    menu_file = join(sysconfdir, 'menus/applications.menu')

    def __init__(self, name):
        self.name = name

    def remove(self):
        pass

    def create(self):
        self._create_dirs()
        self._ensure_menu_file()

        # Create the menu resources.  Note that the .directory
        # files all go in the same directory, so to help ensure uniqueness of
        # filenames we the name.
        d = dict(name=self.name,
                 path=join(datadir, 'desktop-directories',
                                              '%s.directory' % self.name))
        try:
            import custom_tools
            icon_path = join(dirname(custom_tools.__file__), 'menu.ico')
            if isfile(icon_path):
                d['icon'] = icon_path
        except ImportError:
            pass
        make_directory_entry(d)

        tree = ET.parse(self.menu_file)
        root = tree.getroot()

        # Ensure the menu file documents this menu.
        for element in root.findall('Menu'):
            if element.find('Name').text == self.name:
                menu_element = element
                break
        else:
            menu_element = ET.SubElement(root, 'Menu')

        ensure_child_element(menu_element, 'Name', self.name)
        ensure_child_element(menu_element, 'Directory', basename(d['path']))
        include_element = ensure_child_element(menu_element, 'Include')
        ensure_child_element(include_element, 'Category', self.name)
        tree.write(self.menu_file)
        self._add_dtd_and_format()

    def _add_dtd_and_format(self):
        tree = ET.ElementTree(None, self.menu_file)
        indent(tree.getroot())
        fo = open(self.menu_file, 'w')
        fo.write("""\
<!DOCTYPE Menu PUBLIC '-//freedesktop//DTD Menu 1.0//EN'
  'http://standards.freedesktop.org/menu-spec/menu-1.0.dtd'>
""")
        tree.write(fo)
        fo.write('\n')
        fo.close()

    def _create_dirs(self):
        # Ensure the three directories we're going to write menu and shortcut
        # resources to all exist.
        for dir_path in [join(sysconfdir, 'menus'),
                         join(datadir, 'applications'),
                         join(datadir, 'desktop-directories')]:
            if not isdir(dir_path):
                os.makedirs(dir_path)

    def _is_valid_menu_file(self):        
        try:
            tree = ET.parse(self.menu_file)
            root = tree.getroot()
            assert root is not None and root.tag == 'Menu'
            return True
        except:
            return False

    def _ensure_menu_file(self):
        # create a menu file for the top-level menu
        # Ensure any existing version is a file.
        if exists(self.menu_file) and not isfile(self.menu_file):
            shutil.rmtree(self.menu_file)

        # ensure any existing file is actually a menu file
        if isfile(self.menu_file):
            # Make a backup of the menu file to be edited
            cur_time = time.strftime('%Y-%m-%d_%H:%M:%S')
            backup_menu_file = "%s.%s" % (self.menu_file, cur_time)
            shutil.copyfile(self.menu_file, backup_menu_file)

            if not self._is_valid_menu_file():
                os.remove(self.menu_file)

        # create a new menu file if one doesn't yet exist
        if not isfile(self.menu_file):
            fo = open(self.menu_file, 'w')
            fo.write("""\
<Menu>
    <Name>Applications</Name>
    <MergeFile type="parent">/etc/xdg/menus/applications.menu</MergeFile>
</Menu>
""")
            fo.close()


class ShortCut(object):

    fn_pat = re.compile(r'[\w.-]+$')

    def __init__(self, menu, shortcut):
        # Note that this is the path WITHOUT extension
        fn = '%s_%s' % (menu.name, shortcut['id'])
        assert self.fn_pat.match(fn)
        self.path = join(datadir, 'applications', fn)

        shortcut['categories'] = menu.name
        self.shortcut = shortcut
        for var_name in ('name', 'cmd'):
            if var_name in shortcut:
                setattr(self, var_name, shortcut[var_name])

    def create(self):
        self._install_desktop_entry('gnome')
        self._install_desktop_entry('kde')

    def remove(self):
        for ext in ('.desktop', 'KDE.desktop'):
            path = self.path + ext
            rm_rf(path)

    def _install_desktop_entry(self, tp):
        # Handle the special placeholders in the specified command.  For a
        # filebrowser request, we simply used the passed filebrowser.  But
        # for a webbrowser request, we invoke the Python standard lib's
        # webbrowser script so we can force the url(s) to open in new tabs.
        spec = self.shortcut.copy()
        spec['tp'] = tp

        path = self.path
        if tp == 'gnome':
            filebrowser = 'gnome-open'
            path += '.desktop'
        elif tp == 'kde':
            filebrowser = 'kfmclient openURL'
            path += 'KDE.desktop'

        cmd = self.cmd
        if cmd[0] == '{{FILEBROWSER}}':
            cmd[0] = filebrowser
        elif cmd[0] == '{{WEBBROWSER}}':
            import webbrowser
            cmd[0:1] = [sys.executable, webbrowser.__file__, '-t']

        spec['cmd'] = cmd
        spec['path'] = path

        # Create the shortcuts.
        make_desktop_entry(spec)
