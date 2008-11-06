# Copyright (c) 2008 by Enthought, Inc.
# All rights reserved.


import platform
import warnings


def install(menus, shortcuts, install_mode='user'):
    """
    Install an application menu according to the specified mode.

    This call is meant to work on all platforms.  If done on Linux, the menu
    will be installed to both Gnome and KDE desktops if they're available.

    Note that the information required is sufficient to install application
    menus on systems that follow the format of the Desktop Entry Specification
    by freedesktop.org.  See:
            http://freedesktop.org/Standards/desktop-entry-spec

    menus: A list of menu descriptions that will be added/merged into the OS's
        application menu.   A menu description is a dictionary containing the
        following keys and meanings:
            category: An identifier used to locate application link icons
                within a menu.  Note that the string you specify for a sub-menu
                is not the full category as this code will prefix the specified
                string with the parent menu's category, using a '.' as a
                separator char.  For example, if a menu with category 'Abc'
                contains a sub-menu who's category is 'Def', then the full
                category for the sub-menu will be 'Abc.Def'.
            id: A string that can be used to represent the resources needed to
                represent the menu.  i.e. on Linux, the id is used for the name
                of the '.directory' file.  If no category is explicitly
                specified, the id is also capitalized and used as the category
                specification.
            name: The display name of the menu.
            sub-menus: A list of menu descriptions that make up sub-menus of
                this menu.
    shortcuts: A list of shortcut specifications to be created within the
        previously specified menus.   A shortcut specification is a dictionary
        consisting of the following keys and values:
            categories: A list of the menu categories this shortcut should
                appear in.  We only support your own menus at this time due to
                cross-platform difficulties with identifying "standard"
                locations.
            cmd: A list of strings where the first item in the list is the
                executable command and the other items are arguments to be
                passed to that command.   Each argument should be a separate
                item in the list.   Note that you can use the special text
                '{{FILEBROWSER}}' within the first argument to specify that
                the command should use the local file browser command. (It
                differs per desktop, OS, etc.)
            comment: A description for the shortcut.
            id: A string that can be used to represent the resources needed to
                represent the shortcut.  i.e. on Linux, the id is used for the
                name of the '.desktop' file.  If no id is provided, the name
                is lowercased and used as the id.
            name: The display name for the shortcut.
            terminal: A boolean value representing whether the shortcut should
                run within a shell / terminal.
    install_mode: should be either 'user' or 'system' and controls where the
        menus and shortcuts are installed on the system, depending on platform.

    FIXME: We need to add icon support.

    """

    # Validate we have a valid install mode.
    if install_mode != 'user' and install_mode != 'system':
        warnings.warn('Unknown install mode.  Must be either "user" or '
            '"system" but got "%s"' % install_mode)
        return

    # Determine our current platform and version.  This needs to distinguish
    # between, not only different OSes, but also different OS flavors
    # (i.e Linux distributions) and versions of OSes.
    PLAT, PVER = platform.dist()[:2]
    if PLAT.lower().startswith('redhat'):
        PLAT = 'rhel'
        if len(PVER) and PVER[0] in ['3', '4', '5']:
            PVER = PVER[0]

    # Dispatch for RedHat 3.
    if PLAT=='rhel' and PVER=='3':
        from appinst.platforms.rh3 import RH3
        RH3().install_application_menus(menus, shortcuts, install_mode)

    # Dispatch for RedHat 4.
    elif PLAT == 'rhel' and (PVER == '4' or PVER =='5'):
        from appinst.platforms.rh4 import RH4
        RH4().install_application_menus(menus, shortcuts, install_mode)
    
    # Dispatch for OS X
    elif platform.system().lower() == 'darwin':
        from appinst.platforms.osx import OSX
        OSX().install_application_menus(menus, shortcuts, install_mode)

    # Dispatch for Windows, tested on XP only.
    elif platform.system().lower() == 'windows':
        from appinst.platforms.win32 import Win32
        Win32().install_application_menus(menus, shortcuts, install_mode)

    # Handle all other platforms with a warning until we implement for them.
    else:
        warnings.warn('Unknown platform (%s) and version (%s). Unable '
            'to create application menu(s).' % (PLAT, PVER))

    return
