# Copyright (c) 2008 by Enthought, Inc.
# All rights reserved.


import os
import sys

from appinst.platforms.shortcut_creation_error import ShortcutCreationError
from appinst.platforms import win32_common as common


class Win32(object):
    """
    A class for application installation operations on Windows.

    """

    #==========================================================================
    # Public API methods
    #==========================================================================

    def install_application_menus(self, menus, shortcuts, mode):
        """
        Install application menus.

        """

        try:
            if mode == 'system':
                start_menu = common.get_all_users_programs_start_menu()
            else:
                start_menu = common.get_current_user_programs_start_menu()
            self._install_application_menus(menus, shortcuts, start_menu)
        except ShortcutCreationError, ex:
            warnings.warn(ex.message)

        return


    #==========================================================================
    # Internal API methods
    #==========================================================================

    def _install_application_menus(self, menus, shortcuts, start_menu):

        # Create the menus
        queue = [(menu_spec, start_menu,'') for menu_spec in menus]
        category_map = {}
        while len(queue) > 0:
            menu_spec, parent_dir, parent_category = queue.pop(0)

            # Ensure we have a directory representing this menu.
            dir_path = os.path.join(parent_dir, menu_spec['name'])
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

            # Map the category of this menu to its location for use when
            # creating the shortcuts.  Note that if the category wasn't
            # explicitly specified, we use the capitalized version of the id.
            category = menu_spec.get('category',
                menu_spec.get('id').capitalize())
            if len(parent_category) > 1:
                category = '%s.%s' % (parent_category, category)
            category_map[category] = dir_path

            # Put all sub-menus onto the queue to be created.
            for child_spec in menu_spec.get('sub-menus', []):
                queue.append((child_spec, dir_path, category))

        # Install the shortcutsE
        for shortcut in shortcuts:
            for mapped_category in shortcut['categories']:

                # Windows explorer is automatically launched when a folder link
                # is selected, so {{FILEBROWSER}} (which specifies the file
                # manager on linux) can be removed.  There is also a webbrowser
                # check which returns '' on windows, so we should check for that
                # as well.
                args = []
                cmd = shortcut['cmd']
                if cmd[0] == '{{FILEBROWSER}}' or cmd[0] == '':
                    del cmd[0]
                if len(cmd) > 1:
                    args = cmd[1:]

                # Create the actual link with the following arguments:
                # path to original file, description, path to link file,
                # command-line arguments
                target_name = os.path.basename(cmd[0])
                common.add_shortcut(cmd[0], shortcut['comment'],
                    os.path.join(category_map[mapped_category],
                        target_name + ".lnk"),
                    *args)

        return

