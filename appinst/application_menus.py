# Copyright (c) 2008 by Enthought, Inc.
# All rights reserved.

import os
import platform
import warnings


CUSTOM_DIR = (sys.platform=='win32') and os.path.join(sys.prefix, 'Lib', 'custom_tools') or \
    glob.glob(os.path.join(sys.prefix, 'lib', 'python*', 'custom_tools'))[0]
PROPERTIES_FILE = os.path.join(CUSTOM_DIR, 'Property.dat')
PROPERTY_DAT = False
if os.path.exists(PROPERTIES_FILE):
    PROPERTY_DAT = True

def determine_platform():
    # Determine our current platform and version.  This needs to distinguish
    # between, not only different OSes, but also different OS flavors
    # (i.e Linux distributions) and versions of OSes.
    plat = platform.system().lower()
    if plat == 'linux':
        plat, pver = platform.dist()[:2]
    elif plat == 'windows':
        pver = platform.win32_ver()[0]
    elif plat == 'darwin':
        pver = platform.mac_ver()[0]
    
    return plat, pver


def get_system_defaults():

    f = open(PROPERTIES_FILE, 'r')
    defaults = {}
    while 1:
        line = f.readline().strip()
        if not line:
            break
        if line.startswith('#'):
            continue
        key, value = line.split('=')
        defaults[key.strip()] = value.strip()
    f.close()

    return defaults


def get_default_menu(defaults):

    DEFAULT_MENU = [
        { # top-level menu
            'id': defaults['Manufacturer'].lower(),
            'name': defaults['Manufacturer'],
            'sub-menus': [
                { # versioned sub-menu
                    'id': '%(Name)s %(ProductVersion)s'.lower() % defaults,
                    'name': defaults['ProductName'],
                    },
                ],
            },
        ]

    return DEFAULT_MENU


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
            category: An optional identifier used to locate shortcuts within a
                menu.  Note that the string you specify here is not necessarily
                the full category you'll need to use in your shortcut as this
                package ensures uniqueness of category values by concatenating
                them as it goes down the menu hierarchy, using a '.' as the
                separator char.  For example, if a menu with category 'Abc'
                contains a sub-menu who's category is 'Def', then the full
                category for the sub-menu will be 'Abc.Def'.
            id: A string that can be used to represent the resources needed to
                represent the menu.  i.e. on Linux, the id is used for the name
                of the '.directory' file.  If no category is explicitly
                specified, the id is capitalized and used as the category
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
                markers listed here as the first command string to represent
                standard commands that are platform dependent:

                '{{FILEBROWSER}}' specifies that the following arguments are
                    paths to be opened in the OS's file system explorer.
                '{{WEBBROWSER}}' specifies that the following arguments are
                    paths to be opened in the OS's standard, or user's default,
                    web browser.

            comment: A description for the shortcut, typically becomes fly-over
                help.
            icon: An optional path to an .ico file to use as the icon for this
                shortcut.
            id: A string that can be used to represent the resources needed to
                represent the shortcut.  i.e. on Linux, the id is used for the
                name of the '.desktop' file.  If no id is provided, the name
                is lowercased and used as the id.
            name: The display name for this shortcut.
            terminal: A boolean value representing whether the shortcut should
                run within a shell / terminal.

    install_mode: should be either 'user' or 'system' and controls where the
        menus and shortcuts are installed on the system, depending on platform.

    FIXME: We need to add icon support for menus.

    """

    if PROPERTY_DAT:
        system_defaults = get_system_defaults()
    
        if system_defaults['ALLUSERS'] == '1':
            isntall_mode = 'system'
        else:
            install_mode = 'user'

        if not menus:
            menus = get_default_menu(system_defaults)

    # Validate we have a valid install mode.
    if install_mode != 'user' and install_mode != 'system':
        warnings.warn('Unknown install mode.  Must be either "user" or '
            '"system" but got "%s"' % install_mode)
        return

    plat, pver = determine_platform()

    # Dispatch for RedHat 3.
    if plat.startswith('redhat') and pver[0] == '3':
        from appinst.platforms.rh3 import RH3
        RH3().install_application_menus(menus, shortcuts, install_mode)

    # Dispatch for RedHat 4.
    elif plat.startswith('redhat') and pver[0] == '4':
        from appinst.platforms.rh4 import RH4
        RH4().install_application_menus(menus, shortcuts, install_mode)

    # Dispatch for RedHat 5.
    elif plat.startswith('redhat') and pver[0] == '5':
        from appinst.platforms.rh5 import RH5
        RH5().install_application_menus(menus, shortcuts, install_mode)

    # Dispatch for all versions of OS X
    elif plat == 'darwin':
        from appinst.platforms.osx import OSX
        OSX().install_application_menus(menus, shortcuts, install_mode)

    # Dispatch for all versions of Windows (tested on XP only)
    elif plat == 'windows':
        from appinst.platforms.win32 import Win32
        Win32().install_application_menus(menus, shortcuts, install_mode)

    # Handle all other platforms with a warning until we implement for them.
    else:
        warnings.warn('Unhandled platform (%s) and version (%s). Unable '
            'to create application menu(s).' % (plat, pver))

    return


def uninstall(menus, shortcuts, install_mode='user'):
    """
    Uninstall application menus.
    
    FIXME: This currently only works for Windows which can determine the install
    mode from the registry entry. There should be a method for linux as well
    which determines the installation type possibly from the install directory,
    a stored value, or user input.
    """

    # Validate we have a valid install mode.
    if install_mode != 'user' and install_mode != 'system':
        warnings.warn('Unknown install mode.  Must be either "user" or '
            '"system" but got "%s"' % install_mode)
        return

    plat, pver = determine_platform()

    # Dispatch for all versions of Windows (tested on XP only)
    if plat == 'windows':
        from appinst.platforms.win32 import Win32
        Win32().uninstall_application_menus(menus, shortcuts, install_mode)


