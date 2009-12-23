# Copyright (c) 2008-2009 by Enthought, Inc.
# All rights reserved.

import os
import shutil
import sys
import time
import warnings
import xml.etree.ElementTree as ET
from os.path import abspath, basename, exists, expanduser, isdir, isfile, join

import appinst.platforms.linux_common as common
from appinst.platforms.freedesktop import (filesystem_escape,
                     make_desktop_entry, make_directory_entry)
from appinst.platforms.shortcut_creation_error import ShortcutCreationError
from distutils.sysconfig import get_python_lib


DOCTYPE="""<!DOCTYPE Menu
  PUBLIC '-//freedesktop//DTD Menu 1.0//EN'
  'http://standards.freedesktop.org/menu-spec/menu-1.0.dtd'>
"""

USER_MENU_FILE ="""
<Menu>
    <Name>Applications</Name>
    <MergeFile type="parent">/etc/xdg/menus/applications.menu</MergeFile>
</Menu>
"""

class Linux(object):

    #==========================================================================
    # Public API methods
    #==========================================================================

    def install_application_menus(self, menus, shortcuts, mode):
        """
        Install application menus according to the install mode.

        We install into both KDE and Gnome desktops.  If the mode isn't
        exactly 'system', a user install is done.
        """
        # NOTE: Our installation mechanism works for both KDE and Gnome as
        # shipped with RH 5.  But we don't raise an exception if creation fails
        # because there is no guarantee a user has both KDE and Gnome installed.
        try:
            if mode == 'system':
                self._install_system_application_menus(menus, shortcuts)
            else:
                self._install_user_application_menus(menus, shortcuts)
        except ShortcutCreationError, ex:
            warnings.warn(ex.message)


    #==========================================================================
    # Internal API methods
    #==========================================================================

    def _ensure_child_element(self, parent_element, tag, text=None):
        """
        Ensure there is a sub-element of the specified tag type.

        The sub-element is given the specified text content if text is not
        None.

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


    def _install_application_menus(self, datadir, sysconfdir, menus, shortcuts):
        """
        Create application menus.

        datadir: the directory that should contain the desktop and directory
            entries.
        sysconfdir: the directory that should contain the XML menu files.
        """
        # Safety check to ensure the data and sysconf dirs actually exist.
        for dir_path in [datadir, sysconfdir]:
            if not exists(dir_path):
                raise ShortcutCreationError('Cannot install menus and '
                    'shortcuts due to missing directory: %s' % dir_path)

        # Ensure the three directories we're going to write menu and shortcut
        # resources to all exist.
        for dirs in [[sysconfdir, 'menus', 'applications-merged'], [datadir,
            'applications'], [datadir, 'desktop-directories']]:
            for i in xrange(1, len(dirs)+1):
                cur_dirs = dirs[:i]
                dir_path = join(*cur_dirs)
                if not isdir(dir_path):
                    os.mkdir(dir_path)

        # Create a menu file for just the top-level menus.  Later on, we will
        # add the sub-menus to them, which means we need to record where each
        # one was on the disk, plus its tree (to be able to write it), plus the
        # parent menu element.
        menu_dir = join(sysconfdir, 'menus')
        menu_map = {}
        for menu_spec in menus:
            menu_file = join(menu_dir, '%s.menu' % 'applications')

            # Ensure any existing version is a file.
            if exists(menu_file) and not isfile(menu_file):
                shutil.rmtree(menu_file)

            # Ensure any existing file is actually a menu file.
            if isfile(menu_file):
                try:
                    # Make a backup of the menu file to be edited
                    cur_time = time.strftime('%Y%m%d%H%M%S')
                    backup_menu_file = "%s.%s" % (menu_file, cur_time)
                    shutil.copyfile(menu_file, backup_menu_file)

                    tree = ET.parse(menu_file)
                    root = tree.getroot()
                    if root is None or root.tag != 'Menu':
                        raise Exception('Not a menu file')
                except:
                    os.remove(menu_file)

            # Create a new menu file if one doesn't yet exist.
            if not exists(menu_file):
                f = open(menu_file, 'w')
                f.write(USER_MENU_FILE)
                f.close()
                tree = ET.parse(menu_file)
                root = tree.getroot()

            # Record info about the menu file for use when actually creating the
            # menu records.  We need the path to the file, the tree (so
            # xml.etree can write to the file), and the parent element to create
            # our menu data off of.
            menu_map[id(menu_spec)] = (menu_file, tree, root)

        # Create all menu and sub-menu resources.  Note that the .directory
        # files all go in the same directory, so to help ensure uniqueness of
        # filenames we base them on the category, rather than the menu's ID.
        desktop_dir = join(datadir, 'desktop-directories')
        queue = [(menu_spec, '', '') for menu_spec in menus]
        id_map = {}
        while len(queue) > 0:
            menu_spec, parent_category, parent_id = queue.pop(0)

            # Build an id based on the menu hierarchy that's to be prepended
            # to the id of each shortcut based on where that shortcut fits
            # in the menu.
            menu_id = common.build_id(menu_spec['id'], parent_id)

            # Create the category string for this menu.
            category = menu_spec.get('category',
                menu_spec.get('id').capitalize())
            if len(parent_category) > 1:
                category = '%s.%s' % (parent_category, category)

             # Keep track of which IDs match which categories
            id_map[category] = menu_id

            # Create the .directory entry file and record what it's name was
            # for our later use.
            dict = menu_spec.copy()
            dict['location'] = desktop_dir
            dict['filename'] = filesystem_escape(category)
            entry_path = make_directory_entry(dict)
            entry_filename = basename(entry_path)

            # Ensure the menu file documents this menu.  We do this by updating
            # any existing menu of the same name.
            name = menu_spec['name']
            menu_file, tree, parent_element = menu_map[id(menu_spec)]
            for element in parent_element.findall('Menu'):
                if element.find('Name').text == name:
                    menu_element = element
                    break
            else:
                menu_element = ET.SubElement(parent_element, 'Menu')
            self._ensure_child_element(menu_element, 'Name', name)
            self._ensure_child_element(menu_element, 'Directory',
                entry_filename)
            include_element = self._ensure_child_element(menu_element,
                'Include')
            self._ensure_child_element(include_element, 'Category', category)
            tree.write(menu_file)

            # Add any child sub-menus onto the queue.
            for child_spec in menu_spec.get('sub-menus', []):
                menu_map[id(child_spec)] = (menu_file, tree, menu_element)
                queue.append((child_spec, category, menu_id))

        # Restore DOCTYPE, as the xml lib leaves it out.
        fin = open(menu_file)
        file_xml = fin.read()
        fin.close()
        file_xml = DOCTYPE + file_xml
        fout = open(menu_file, 'w')
        fout.write(file_xml)
        fout.close()

        # Adjust the IDs of the shortcuts to match where the shortcut fits in
        # the menu.
        common.fix_shortcut_ids(shortcuts, id_map)

        # Write out any shortcuts
        location = join(datadir, 'applications')
        self._install_gnome_desktop_entry(shortcuts, location)
        self._install_kde_desktop_entry(shortcuts, location)


    def _install_desktop_entry(self, shortcuts, filebrowser):
        """
        Create a desktop entry for the specified shortcut spec.
        """
        for spec in shortcuts:
            # Handle the special placeholders in the specified command.  For a
            # filebrowser request, we simply used the passed filebrowser.  But
            # for a webbrowser request, we invoke the Python standard lib's
            # webbrowser script so we can force the url(s) to open in new tabs.
            cmd = spec['cmd']
            if cmd[0] == '{{FILEBROWSER}}':
                cmd[0] = filebrowser
            elif cmd[0] == '{{WEBBROWSER}}':
                python_path = join(sys.prefix, 'bin', 'python')
                script_path = abspath(join(get_python_lib(),
                    '..', 'webbrowser.py'))
                cmd[0:1] = [python_path, script_path, '-t']
            spec['cmd'] = cmd

            # Create the shortcuts.
            make_desktop_entry(spec)


    def _install_gnome_desktop_entry(self, shortcuts, location):
        """
        Create a desktop entry for the specified shortcut spec.
        """
        # Iterate though the shortcuts making a copy of each specification and
        # adding an entry so that it doesn't show in the KDE desktop, plus ends
        # up in the specified location.
        modified_shortcuts = []
        for spec in shortcuts:
            cur = spec.copy()
            cur['location'] = location
            cur['not_show_in'] = 'KDE'
            modified_shortcuts.append(cur)

        # Make the shortcuts
        filebrowser = "gnome-open"
        self._install_desktop_entry(modified_shortcuts, filebrowser)


    def _install_kde_desktop_entry(self, shortcuts, location):
        """
        Create a desktop entry for the specified shortcut spec.
        """
        # Iterate though the shortcuts making a copy of each specification and
        # adding an entry so that it only shows in the KDE desktop, plus ends
        # up in the specified location.
        modified_shortcuts = []
        for spec in shortcuts:
            cur = spec.copy()
            cur['location'] = location
            cur['only_show_in'] = 'KDE'
            modified_shortcuts.append(cur)

        # Make the shortcuts
        filebrowser = "kfmclient openURL"
        self._install_desktop_entry(modified_shortcuts, filebrowser)

        # Force the KDE menus to refresh
        retcode = os.system('kbuildsycoca')
        if retcode != 0:
            raise ShortcutCreationError('Unable to rebuild KDE desktop.  '
                'Application menu may not have been installed correctly, '
                'or KDE is not installed.')


    def _install_system_application_menus(self, menus, shortcuts):
        datadir = '/usr/share'
        sysconfdir = '/etc/xdg'

        return self._install_application_menus(datadir, sysconfdir, menus,
                                               shortcuts)


    def _install_user_application_menus(self, menus, shortcuts):
        # Prefer env variable specifications over default values.  The
        # environment variable names are per the Desktop Menu Specification
        # at:
        #     http://standards.freedesktop.org/menu-spec/latest/apcs02.html
        datadir = os.environ.get('XDG_DATA_HOME',
                                 abspath(expanduser('~/.local/share')))
        sysconfdir = os.environ.get('XDG_CONFIG_HOME',
                                    abspath(expanduser('~/.config')))

        # Make sure the target directories exist.
        for dir_path in [datadir, sysconfdir]:
            if not isdir(dir_path):
                if isfile(dir_path):
                    os.remove(dir_path)
                os.makedirs(dir_path)

        # Create our shortcuts.
        return self._install_application_menus(datadir, sysconfdir, menus,
                                               shortcuts)
