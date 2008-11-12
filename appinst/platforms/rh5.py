# Copyright (c) 2008 by Enthought, Inc.
# All rights reserved.


import copy
import os
import shutil
import sys
import time
import warnings
import xml.etree.ElementTree as et

from appinst.platforms.freedesktop import (filesystem_escape,
    make_desktop_entry, make_directory_entry)
from appinst.platforms.shortcut_creation_error import ShortcutCreationError

USER_MENU_FILE ="""
<!DOCTYPE Menu
  PUBLIC '-//freedesktop//DTD Menu 1.0//EN'
  'http://standards.freedesktop.org/menu-spec/menu-1.0.dtd'>
<Menu>
    <Name>Applications</Name>
    <MergeFile type="parent">/etc/xdg/menus/applications.menu</MergeFile>
</Menu>
"""

class RH5(object):
    """
    A class for application installation operations on RH5.

    """

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
        # shipped with RH 4.

        try:
            if mode == 'system':
                self._install_system_application_menus(menus, shortcuts)
            else:
                self._install_user_application_menus(menus, shortcuts)
        except ShortcutCreationError, ex:
            warnings.warn(ex.message)

        return


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
            element = et.SubElement(parent_element, tag)

        # If specified, set its text
        if text is not None:
            element.text = text

        return element


    def _install_application_menus(self, datadir, sysconfdir, menus,
        shortcuts):
        """
        Create application menus.

        datadir: the directory that should contain the desktop and directory
            entries.
        sysconfdir: the directory that should contain the XML menu files.

        """

        # Safety check to ensure the data and sysconf dirs actually exist.
        for dir in [datadir, sysconfdir]:
            if not os.path.exists(dir):
                raise ShortcutCreationError('Cannot install menus and '
                    'shortcuts due to missing directory: %s' % dir)

        # Ensure the three directories we're going to write menu and shortcut
        # resources to all exist.
        for dirs in [[sysconfdir, 'menus', 'applications-merged'], [datadir,
            'applications'], [datadir, 'desktop-directories']]:
            for i in xrange(1, len(dirs)+1):
                cur_dirs = dirs[:i]
                dir = os.path.join(*cur_dirs)
                if not os.path.isdir(dir):
                    os.mkdir(dir)

        # Create a menu file for just the top-level menus.  Later on, we will
        # add the sub-menus to them, which means we need to record where each
        # one was on the disk, plus its tree (to be able to write it), plus the
        # parent menu element.
        # FIXME: xml.etree doesn't seem to support preserving or setting of
        # DOCTYPE.   We may have to switch to a different xml lib?
        menu_dir = os.path.join(sysconfdir, 'menus')
        menu_map = {}
        for menu_spec in menus:
            menu_file = os.path.join(menu_dir, '%s.menu' % 'applications')

            # Ensure any existing version is a file.
            if os.path.exists(menu_file) and not os.path.isfile(menu_file):
                shutil.rmtree(menu_file)

            # Ensure any existing file is actually a menu file.
            if os.path.isfile(menu_file):
                try:
                    # Make a backup of the menu file to be edited
                    cur_time = time.strftime('%Y%m%d%H%M%S')
                    backup_menu_file = "%s.%s" % (menu_file, cur_time)
                    shutil.copyfile(menu_file, backup_menu_file)

                    tree = et.parse(menu_file)
                    root = tree.getroot()
                    if root is None or root.tag != 'Menu':
                        raise Exception('Not a menu file')
                except:
                    os.remove(menu_file)

            # Create a new menu file if one doesn't yet exist.
            if not os.path.exists(menu_file):
                f = open(menu_file, 'w')
                f.write(USER_MENU_FILE)
                f.close()
                tree = et.parse(menu_file)
                root = tree.getroot()

            # Record info about the menu file for use when actually creating the
            # menu records.  We need the path to the file, the tree (so
            # xml.etree can write to the file), and the parent element to create
            # our menu data off of.
            menu_map[id(menu_spec)] = (menu_file, tree, root)

        # Create all menu and sub-menu resources.  Note that the .directory
        # files all go in the same directory, so to help ensure uniqueness of
        # filenames we base them on the category, rather than the menu's ID.
        desktop_dir = os.path.join(datadir, 'desktop-directories')
        queue = [(menu_spec, '') for menu_spec in menus]
        while len(queue) > 0:
            menu_spec, parent_category = queue.pop(0)

            # Create the category string for this menu.
            category = menu_spec.get('category',
                menu_spec.get('id').capitalize())
            if len(parent_category) > 1:
                category = '%s.%s' % (parent_category, category)

            # Create the .directory entry file and record what it's name was
            # for our later use.
            dict = menu_spec.copy()
            dict['location'] = desktop_dir
            dict['filename'] = filesystem_escape(category)
            entry_path = make_directory_entry(dict)
            entry_filename = os.path.basename(entry_path)

            # Ensure the menu file documents this menu.  We do this by updating
            # any existing menu of the same name.
            name = menu_spec['name']
            menu_file, tree, parent_element = menu_map[id(menu_spec)]
            for element in parent_element.findall('Menu'):
                if element.find('Name').text == name:
                    menu_element = element
                    break
            else:
                menu_element = et.SubElement(parent_element, 'Menu')
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
                queue.append((child_spec, category))

        # Write out any shortcuts
        location = os.path.join(datadir, 'applications')

        self._install_gnome_desktop_entry(shortcuts, location)
        self._install_kde_desktop_entry(shortcuts, location)
        # Force the menus to refresh.

        return


    def _install_kde_desktop_entry(self, shortcuts, location):
        """
        Create a desktop entry for the specified shortcut spec.

        """

        file_browser = "kfmclient openURL"

        for spec in shortcuts:
            spec_dict = copy.deepcopy(spec)

            # Replace any 'FILEBROWSER' placeholder in the command with the
            # specified value.
            cmd = spec_dict['cmd']
            cmd[0] = cmd[0].replace('{{FILEBROWSER}}', file_browser)

            # Store the desired target location for the entry file.
            spec_dict['location'] = location

            spec_dict['only_show_in'] = 'KDE'

            # Make it.
            make_desktop_entry(spec_dict)

        retcode = os.system('kbuildsycoca')
        if retcode != 0:
            raise ShortcutCreationError('Unable to rebuild desktop.  '
                'Application menu may not have been installed correctly,'
                ' or KDE is not installed.')

        return

    def _install_gnome_desktop_entry(self, shortcuts, location):
        """
        Create a desktop entry for the specified shortcut spec.

        """
        file_browser = "gnome-open"

        for spec in shortcuts:
            spec_dict = copy.deepcopy(spec)

            # Replace any 'FILEBROWSER' placeholder in the command with the
            # specified value.
            cmd = spec_dict['cmd']
            cmd[0] = cmd[0].replace('{{FILEBROWSER}}', file_browser)

            # Store the desired target location for the entry file.
            spec_dict['location'] = location

            spec_dict['not_show_in'] = 'KDE'

            # Make it.
            make_desktop_entry(spec_dict)

        return

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
        datadir = os.environ.get('XDG_DATA_HOME', os.path.abspath(
            os.path.join(os.path.expanduser('~'), '.local', 'share')))
        sysconfdir = os.environ.get('XDG_CONFIG_HOME', os.path.abspath(
            os.path.join(os.path.expanduser('~'), '.config')))

        # Make sure the target directories exist.
        for dir in [datadir, sysconfdir]:
            if not os.path.isdir(dir):
                if os.path.isfile(dir):
                    os.remove(dir)
                os.makedirs(dir)

        # Create our shortcuts.
        return self._install_application_menus(datadir, sysconfdir, menus,
            shortcuts)


