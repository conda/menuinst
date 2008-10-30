import appinst.platforms.win32_common as common
import os
import sys
from appinst.platforms.shortcut_creation_error import ShortcutCreationError

class Win32(object):
    """
    A class for application installation operations on windows.

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
                start_menu = common._get_all_users_programs_start_menu()
            else:
                start_menu = common._get_current_user_programs_start_menu()
            self._install_application_menus(menus, shortcuts, start_menu)
        except ShortcutCreationError, ex:
            warnings.warn(ex.message)

        return

    #==========================================================================
    # Internal API methods
    #==========================================================================

    def _install_application_menus(self, menus, shortcuts, start_menu):
        dir_path = start_menu
        queue = [(menu_spec, '') for menu_spec in menus]
        category_map = {}
        while len(queue) > 0:
            menu_spec, parent_category = queue.pop(0)
            
            # Directory name should match the menu name
            dir_path = os.path.join(dir_path, menu_spec['name'])
        
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            
            # id's of the menus will be mapped to categories of the shortcuts
            # if no category is present. This determines which directories to
            # put shortcuts in
            category = menu_spec.get('category',
                menu_spec.get('id').capitalize())

            if len(parent_category) > 1:
                category = '%s.%s' % (parent_category, category)

            category_map[category] = dir_path

            for child_spec in menu_spec.get('sub-menus', []):
                queue.append((child_spec, category))

        for shortcut in shortcuts:
            for mapped_category in shortcut['categories']:
                cmd = shortcut['cmd']
                args = []
                # Windows explorer is automatically launched when a folder link
                # is selected, so {{FILEBROWSER}} (which specifies the file
                # manager on linux) can be removed.
                # There is also a webbrowser check which returns '' on windows,
                # so we should check for that as well.
                if cmd[0] == '{{FILEBROWSER}}' or cmd[0] == '':
                    del cmd[0]
                # In case the command has arguements, e.g. ipython -pylab
                if len(cmd) > 1:
                    args = cmd[1:]

                target_name = os.path.basename(cmd[0])

                # Create the actual link with the following arguments:
                # path to original file, description, path to link file,
                # command-line arguments
                common.add_shortcut(cmd[0], shortcut['comment'],
                    os.path.join(category_map[mapped_category],
                        target_name + ".lnk"),
                    *args)
