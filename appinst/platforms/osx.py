# Copyright (c) 2008-2009 by Enthought, Inc.
# All rights reserved.

import os
import sys

from appinst.platforms.shortcut_creation_error import ShortcutCreationError
from appinst.platforms.osx_application import Application


class Executable(Application):

    def write_script(self):
        """
        Creates a 'proxy' bash script.
        Overwrites method.  Requires self.bash_path and self.argv to be set.
        """
        fo = open(self.proxy_path, 'w')
        fo.write("#!/bin/sh\n%s\n" % ' '.join(self.argv))
        fo.close()

        os.chmod(self.proxy_path, 0755)



class OSX(object):
    """
    A class for application installation operations on Mac OS X.

    """

    #==========================================================================
    # Public API methods
    #==========================================================================

    def install_application_menus(self, menus, shortcuts, mode):
        """
        Install application menus.

        """

        self._install_application_menus(menus, shortcuts)

        return

    #==========================================================================
    # Internal API methods
    #==========================================================================

    def _install_application_menus(self, menus, shortcuts):

        # First build all the requested menus.  These correspond simply to
        # directories on OS X.  Note that we need to build a map from the menu's
        # category to its path on the filesystem so that we can put the
        # shortcuts in the right directories later.
        self.category_map = {}
        app_path = '/Applications'
        queue = [(menu_spec, app_path, '') for menu_spec in menus]
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
            self.category_map[category] = path

            # Add all sub-menus to the queue so they get created as well.
            for child_spec in menu_spec.get('sub-menus', []):
                queue.append((child_spec, path, category))

        # Now create all the requested shortcuts.
        SHELL_SCRIPT ="#!/bin/sh\n%s %s\n"
        for shortcut in shortcuts:

            # Ensure the shortcut ends up in each of the requested categories.
            for mapped_category in shortcut['categories']:

                # Install the actual item
                self._install_shortcut(mapped_category, shortcut)

        return


    def _install_shortcut(self, mapped_category, shortcut):

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
        # double-clickable shell script that will execute it.
        if os.path.isfile(cmd) and os.access(cmd, os.X_OK):
            fn = shortcut['name'] + '.command'
            path = os.path.join(category_map[mapped_category], fn)
            fo = open(path, 'w')
            fo.write("#!/bin/sh\n")
            fo.write("%s %s\n" % (cmd, ' '.join(args)))
            fo.close()
            os.chmod(path, 0755)

        # Otherwise, just create a symlink to the specified command
        # value.  Note that it is possible we may only need this logic
        # as symlinks to executable scripts are double-clickable on
        # OS X 10.5 (though there would be no way to apply custom icons
        # then.)
        else:
            name = shortcut['name']
            path = os.path.join(self.category_map[mapped_category], name)
            if os.path.exists(path) and os.path.isfile(path):
                os.remove(path)
            os.symlink(cmd, path)

        return
