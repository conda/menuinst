# Copyright (c) 2008 by Enthought, Inc.
# All rights reserved.

import os
import shutil
import sys
import warnings
from distutils.sysconfig import get_python_lib
from xml.etree import ElementTree

import appinst.platforms.linux_common as common
from appinst.platforms.freedesktop import (filesystem_escape,
                    make_desktop_entry, make_directory_entry)
from appinst.platforms.utils import ShortcutCreationError



class RH3(object):
    """
    A class for application installation operations on RH3.
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
        # Try installing KDE shortcuts.  We don't raise an exception on an
        # error because we don't know if this user has KDE installed.
        try:
            if mode == 'system':
                self._install_kde_system_application_menus(menus, shortcuts)
            else:
                self._install_kde_user_application_menus(menus, shortcuts)
        except ShortcutCreationError, ex:
            warnings.warn(ex.message)

        # Try installing Gnome shortcuts.  We don't raise an exception on an
        # error because we don't know if this user has Gnome installed.
        try:
            if mode == 'system':
                self._install_gnome_system_application_menus(menus, shortcuts)
            else:
                self._install_gnome_user_application_menus(menus, shortcuts)
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
            element = ElementTree.SubElement(parent_element, tag)

        # If specified, set its text
        if text is not None:
            element.text = text

        return element


    def _install_desktop_entry(self, shortcuts, category_map, filebrowser,
                               write_categories = False):
        """
        Create a desktop entry for the specified shortcut spec.
        """
        for spec in shortcuts:
            spec_dict = spec.copy()

            # Handle the special placeholders in the specified command.  For a
            # filebrowser requiest, we simply used the passed filebrowser.  But
            # for a webbrowser request, we invoke the Python standard lib's
            # webbrowser script so we can force the url(s) to open in new tabs.
            cmd = spec['cmd']
            if cmd[0] == '{{FILEBROWSER}}':
                cmd[0] = filebrowser
            elif cmd[0] == '{{WEBBROWSER}}':
                python_path = os.path.join(sys.prefix, 'bin', 'python')
                script_path = os.path.abspath(os.path.join(get_python_lib(),
                    '..', 'webbrowser.py'))
                cmd[0:1] = [python_path, script_path, '-t']
            spec_dict['cmd'] = cmd

            # Remove the categories if they weren't desired.
            if not write_categories:
                del spec_dict['categories']

            # Handle the situation where the shortcut is supposed to be in
            # multiple categories.
            for category in spec['categories']:
                spec_dict['location'] = category_map[category]
                make_desktop_entry(spec_dict)


    def _install_gnome_application_menus(self, vfolder_dir, vfolder_info, menus,
                                         shortcuts):
        """
        Create Gnome2 application menus.

        vfolder_dir: the location to place .directory files within.
        vfolder_info: the configuration file to store the menu info within.
        """
        # Open up the configuration file so we can modify it.
        info_tree = ElementTree.parse(vfolder_info)
        info_root = info_tree.getroot()

        # Top-level menus are represented by a 'MergeDir' entry in the info file
        # and an actual file system directory.  Ensure both of those exist.
        # Note that these are always children of the root 'VFolderInfo' element.
        for menu_spec in menus:

            # Ensure the actual file system directory exists.  We overwrite any
            # existing file of the same name.
            dir_name = filesystem_escape(menu_spec['name'])
            path = os.path.abspath(os.path.join(vfolder_dir, dir_name))
            if not os.path.isdir(path):
                if os.path.exists(path):
                    os.remove(path)
                os.mkdir(path)

            # Ensure the info entry exists.
            for element in info_root.findall('MergeDir'):
                if element.text == path:
                    break
            else:
                element = ElementTree.SubElement(info_root, 'MergeDir')
                element.text = path

        # Find the "Applications" element.
        app_folder_element = None
        for element in info_root.findall('Folder'):
            if element.find('Name').text == 'Applications':
                app_folder_element = element
                break
        if app_folder_element is None:
            raise ShortcutCreationError("Cannot find Gnome's Applications menu")

        # Create the necessary representations for each menu being installed.
        category_map = {'': vfolder_dir}
        queue = [(menu_spec, app_folder_element, vfolder_dir, '', '') \
            for menu_spec in menus]
        id_map = {}
        while len(queue) > 0:
            menu_spec, parent_element, parent_dir, parent_category, parent_id = \
                queue.pop(0)
            name = menu_spec['name']

            # Ensure the actual file system directory exists.  We overwrite any
            # existing file of the same name.
            fs_name = filesystem_escape(name)
            path = os.path.abspath(os.path.join(parent_dir, fs_name))
            if not os.path.isdir(path):
                if os.path.exists(path):
                    os.remove(path)
                os.mkdir(path)

            # Build an id based on the menu hierarchy that's to be prepended
            # to the id of each shortcut based on where that shortcut fits
            # in the menu.
            menu_id = common.build_id(menu_spec['id'], parent_id)

            # Map the category for this menu to its directory path.
            category = menu_spec.get('category', menu_spec['id'])
            if len(parent_category) > 1:
                category = '%s.%s' % (parent_category, category)
            category_map[category] = path

            # Keep track of which IDs match which categories
            id_map[category] = menu_id

            # Create a directory entry file for the current menu.  Because we
            # put all these directly in the vfolder_dir, we base the filename
            # off the category which is more likely to be unique.
            entry_name = os.path.basename(make_directory_entry(
                {'name': name, 'location': vfolder_dir,
                'filename': '%s' % filesystem_escape(category)}))

            # Ensure a Folder element exists for the current menu.
            for element in parent_element.findall('Folder'):
                if element.find('Name').text == name:
                    cur_element = element
                    break
            else:
                cur_element = ElementTree.SubElement(parent_element, 'Folder')
            self._ensure_child_element(cur_element, 'Name', name)
            self._ensure_child_element(cur_element, 'Directory', entry_name)
            query_element = self._ensure_child_element(cur_element, 'Query')
            and_element = self._ensure_child_element(query_element, 'And')
            self._ensure_child_element(and_element, 'Keyword', category)

            # Add any child sub-menus onto the queue.
            for child_spec in menu_spec.get('sub-menus', []):
                queue.append((child_spec, cur_element, path, category, menu_id))

        # We are done with the vfolder, write it back out
        info_tree.write(vfolder_info)

        # Adjust the IDs of the shortcuts to match where the shortcut fits in
        # the menu.
        common.fix_shortcut_ids(shortcuts, id_map)

        # Write out any shortcuts
        filebrowser = "nautilus"
        self._install_desktop_entry(shortcuts, category_map, filebrowser,
                                    write_categories = True)


    def _install_gnome_system_application_menus(self, menus, shortcuts):

        # Ensure the vfolder directory exists.
        vfolder_dir = '/usr/share/desktop-menu-files'
        if not os.path.exists(vfolder_dir):
            raise ShortcutCreationError('Could not find %s' % vfolder_dir)

        # Ensure the vfolder info file exists.
        vfolder_info = '/etc/X11/desktop-menus/applications.menu'
        if not os.path.exists(vfolder_info):
            raise ShortcutCreationError('Could not find %s' % vfolder_info)

        # Create the shortcuts.
        self._install_gnome_application_menus(vfolder_dir, vfolder_info, menus,
            shortcuts)


    def _install_gnome_user_application_menus(self, menus, shortcuts):

        # Check if the user uses Gnome by checking if the '.gnome2' dir exists
        gnome_dir = os.path.abspath(os.path.join(os.path.expanduser("~"),
            ".gnome2"))
        if not os.path.exists(gnome_dir):
            raise ShortcutCreationError('No user .gnome2 directory found')

        # Make sure a vfolders directory exists.
        vfolder_dir = os.path.join(gnome_dir, "vfolders")
        if not os.path.exists(vfolder_dir):
            os.mkdir(vfolder_dir)

        # Ensure a corresponding vfolder information file exists.  We copy the
        # system one if we need to.
        vfolder_info = os.path.join(vfolder_dir, 'applications.vfolder-info')
        if not os.path.exists(vfolder_info):
            sys_vfolder_info = '/etc/X11/desktop-menus/applications.menu'
            if not os.path.exists(sys_vfolder_info):
                raise ShortcutCreationError('Cannot find template '
                '"applications.menu" file to create user vfolder info file '
                'from.')
            shutil.copyfile(sys_vfolder_info, vfolder_info)

        # Create the application menus.
        self._install_gnome_application_menus(vfolder_dir, vfolder_info, menus,
            shortcuts)


    def _install_kde_application_menus(self, share_dir, menus, shortcuts):
        """
        Create KDE application menus.

        share_dir: the file system path to the directory that the application
            menu should be generated wtihin.
        """
        # Safety check to ensure the share dir actually exists.
        if not os.path.exists(share_dir):
            raise ShortcutCreationError('No %s directory found' % share_dir)

        # Find applnk directory.
        # FIXME: Should we be using the 'kde-config' command to find either the
        # paths where it looks for 'apps' resources
        # (i.e. kde-config --path apps) or to get the prefix to install
        # resource files to. (i.e. kde-config --install apps)
        applnk_dir = None
        for dir in os.listdir(share_dir):
            if dir.startswith("applnk"):
                applnk_dir = os.path.join(share_dir, dir)
        if applnk_dir is None:
            raise ShortcutCreationError('Cannot find KDE applnk directory')

        # Create a directory for each menu and sub-menu.  Along the way, record
        # the directory location in a map against the category specification
        # for the menu.
        category_map = {'':applnk_dir}
        queue = [(applnk_dir, menu_spec, '', '') for menu_spec in menus]
        id_map = {}
        while len(queue) > 0:
            root_dir, menu_spec, parent_category, parent_id = queue.pop(0)

            # Create the directory for the current menu overwriting any file
            # of the same name.
            dir_name = filesystem_escape(menu_spec['name'])
            path = os.path.join(root_dir, dir_name)
            if not os.path.isdir(path):
                if os.path.exists(path):
                    os.remove(path)
                os.mkdir(path)

            # Build an id based on the menu hierarchy that's to be prepended
            # to the id of each shortcut based on where that shortcut fits
            # in the menu.
            menu_id = common.build_id(menu_spec['id'], parent_id)

            # Map the category for this menu to its directory path.
            category = menu_spec.get('category', menu_spec['id'])
            if len(parent_category) > 1:
                category = '%s.%s' % (parent_category, category)
            category_map[category] = path

            # Keep track of which IDs match which categories
            id_map[category] = menu_id

            # Add any child sub-menus onto the queue.
            for child_spec in menu_spec.get('sub-menus', []):
                queue.append((path, child_spec, category, menu_id))

        # Adjust the IDs of the shortcuts to match where the shortcut fits in
        # the menu.
        common.fix_shortcut_ids(shortcuts, id_map)

        # Write out any shortcuts
        filebrowser = "kfmclient openURL"
        self._install_desktop_entry(shortcuts, category_map, filebrowser)

        # Force the menus to refresh.
        retcode = os.system('kbuildsycoca')
        if retcode != 0:
            raise ShortcutCreationError('Unable to rebuild KDE desktop.  '
                'Application menu may not have been installed correctly.')


    def _install_kde_system_application_menus(self, menus, shortcuts):

        return self._install_kde_application_menus('/usr/share', menus,
                                                   shortcuts)


    def _install_kde_user_application_menus(self, menus, shortcuts):

        # Check if the user uses KDE by checking if the '.kde/share' dir exists
        share_dir = os.path.abspath(os.path.join(os.path.expanduser('~'),
            '.kde', 'share'))
        if not os.path.exists(share_dir):
            raise ShortcutCreationError('No user .kde directory found')

        # Create our shortcuts under the share dir.
        return self._install_kde_application_menus(share_dir, menus, shortcuts)
