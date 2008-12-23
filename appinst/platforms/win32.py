# Copyright (c) 2008 by Enthought, Inc.
# All rights reserved.


import os
import sys

from appinst.platforms.shortcut_creation_error import ShortcutCreationError
from appinst.platforms import win32_common as common
from distutils.sysconfig import get_python_lib


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

        if mode == 'system':
            start_menu = common.get_all_users_programs_start_menu()
        else:
            start_menu = common.get_current_user_programs_start_menu()
        self._install_application_menus(menus, shortcuts, start_menu)

        return
    
    
    def uninstall_application_menus(self, menus, shortcuts):
        """
        Uninstall application menus.
        """

        start_menu = common.get_programs_start_menu()
        self._uninstall_application_menus(menus, shortcuts, start_menu)

    #==========================================================================
    # Internal API methods
    #==========================================================================

    def _install_application_menus(self, menus, shortcuts, start_menu):

        # First build all the requested menus.  These correspond simply to
        # directories on Win32 systems.  Note that we need to build a map from
        # the menu's category to its path on the filesystem so that we can put
        # the shortcuts in the right directories later.
        category_map = {}
        queue = [(menu_spec, start_menu,'') for menu_spec in menus]
        while len(queue) > 0:
            menu_spec, parent_path, parent_category = queue.pop(0)

            # Create the directory that represents this menu.
            path = os.path.join(parent_path, menu_spec['name'])
            if not os.path.exists(path):
                os.makedirs(path)

            # Determine the category for this menu and record it in the map.
            # Categories are always hierarchical to ensure uniqueness.  Note
            # that if no category was explicitly set, we use the capitalized
            # version of the ID.
            category = menu_spec.get('category',
                menu_spec.get('id').capitalize())
            if len(parent_category) > 1:
                category = '%s.%s' % (parent_category, category)
            category_map[category] = path

            # Add all sub-menus to the queue so they get created as well.
            for child_spec in menu_spec.get('sub-menus', []):
                queue.append((child_spec, path, category))

        # Now create all the requested shortcuts.
        for shortcut in shortcuts:

            # Ensure the shortcut ends up in each of the requested categories.
            for mapped_category in shortcut['categories']:

                # Separate the arguments to the invoked command from the command
                # itself.
                cmd_list = shortcut['cmd']
                cmd = cmd_list[0]
                if len(cmd_list) > 1:
                    args = cmd_list[1:]
                else:
                    args = []

                # Handle the special '{{FILEBROWSER}}' command by stripping it
                # out since File Explorer will automatically be launched when a
                # folder link is separated.
                if cmd == '{{FILEBROWSER}}':
                    cmd = args[0]
                    if len(args) > 1:
                        args = args[1:]
                    else:
                        args = []

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
                    cmd = os.path.join(sys.prefix, 'python.exe')
                    args = [os.path.abspath(os.path.join(get_python_lib(), '..',
                        'webbrowser.py')), '-t'] + args

                # Now create the actual Windows shortcut.  Note that the API to
                # create a windows shortcut requires that a path to the icon
                # file be in a weird place -- second in a variable length
                # list of args.
                name = shortcut['name'] + '.lnk'
                path = os.path.join(category_map[mapped_category], name)
                description = shortcut['comment']
                cmd_args = ' '.join(args)
                icon = shortcut.get('icon', None)
                if not icon:
                    shortcut_args = []
                else:
                    shortcut_args = ['', icon]
                common.add_shortcut(cmd, description, path, cmd_args,
                    *shortcut_args)

        return


    def _uninstall_application_menus(self, menus, shortcuts, start_menu):

        # Keep track of the shortcut names, as the shortcuts we specify are the
        # only things we want to delete. Append '.lnk' to the name because
        # that's how they were created during install.
        shortcut_names = []
        for shortcut in shortcuts:
            shortcut_names.append(shortcut['name'] + '.lnk')

        for top_menu in menus:
            top_name = top_menu['name']
            top_path = os.path.join(start_menu, top_name)

            # Keep track of possible menu directories to be deleted
            menu_paths = [top_path]

            for root, dirs, files in os.walk(top_path):
                for file in files:
                    if file in shortcut_names:
                        file_path = os.path.join(root, file)
                        os.remove(file_path)
                        print "Removed %s" % file_path
                for d in dirs:
                    # Prepend paths so that when we try to delete menu
                    # directories we start at the bottom-most directory
                    menu_paths.insert(0, os.path.join(root, d))

            # Delete menu directories. This should start from the bottom-most
            # directory and work its way up to the top-most. Only directories 
            # that have been emptied will be deleted.
            # FIXME: This will also delete directories that already are empty
            # (not necessarily ones that we created), but that may be a
            # non-issue.
            for menu_path in menu_paths:
                try:
                    os.rmdir(menu_path)
                    print "Removed %s" % menu_path
                except:
                    print "%s not empty, skipping." % menu_path
                    continue
