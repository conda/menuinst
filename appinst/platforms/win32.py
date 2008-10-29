from appinst import common
import os
import sys

class win32(object):
    """
    A class for application installation operations on windows.

    """

    #==========================================================================
    # Public API methods
    #==========================================================================

    def install_application_menus(self, menus, shortcuts):
        """
        Install application menus. Install mode is determined by the 
        common module.

        """

        try:
            self._install_application_menus(menus, shortcuts)
        except ShortcutCreationError, ex:
            warnings.warn(ex.message)

        return

    #==========================================================================
    # Internal API methods
    #==========================================================================

    def _install_application_menus(menus, shortcuts):
        # This determines where the shortcuts will go by checking it the install
        # was for 'All Users' or not
        dir_path = common.get_programs_start_menu()

        queue = [(menu_spec, '') for menu_spec in menus]
        category_map = {}
        while len(queue) > 0:
            menu_spec, parent_category = queue.pop(0)
        
            category = menu_spec.get('category',
                menu_spec.get('id').capitalize())
            
            dir_path = os.path.join(dir_path, category)
        
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        
            if len(parent_category) > 1:
                category = '%s.%s' % (parent_category, category)
        
            category_map[category] = dir_path
        
            name = menu_spec['name']
        
            for child_spec in menu_spec.get('sub-menus', []):
                queue.append((child_spec, category))
        
        for shortcut in shortcuts:
            for mapped_category in shortcut['categories']:
                cmd = shortcut['cmd']
                args = []
                # The FILEBROWSER placeholder is linux-specific, so it can be removed
                # and the '' is the result of getwebbrowser
                if cmd[0] == '{{FILEBROWSER}}' or cmd[0] == '':
                    del cmd[0]
                # In case the command has arguements, e.g. ipython -pylab
                if len(cmd) > 1:
                    args = cmd[1:]
                target_name = os.path.basename(cmd[0])
                common.add_shortcut(cmd[0], shortcut['comment'],
                    os.path.join(category_map[mapped_category], target_name + ".lnk"),
                    *args)
