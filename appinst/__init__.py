# Copyright (c) 2008-2011 by Enthought, Inc.
# All rights reserved.

import sys
from os.path import abspath, dirname, isfile, join

from egginst.utils import bin_dir_name

# The custom_tools package is importable when the Python was created by an
# "enicab" installer, in which case the directory custom_tools contains
# platform-independent install information in __init__.py and platform-specific
# information about user setting chosen during the install process.
try:
    import custom_tools
    menu_name = custom_tools.FULL_NAME
except ImportError:
    menu_name = 'Python-%i.%i' % sys.version_info[:2]


def dispatched_install(shortcuts, remove):
    """
    Install application shortcuts.

    This call is meant to work on all platforms.  If done on Linux, the menu
    will be installed to both Gnome and KDE desktops if they are available.

    Note that the information required is sufficient to install application
    menus on systems that follow the format of the Desktop Entry Specification
    by freedesktop.org.  See:
            http://freedesktop.org/Standards/desktop-entry-spec

    A list of shortcut specifications to be created within the menu.
    A shortcut specification is a dictionary consisting of the following
    keys and values:

    cmd:        A list of strings where the first item in the list is the
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

    comment:    A description for the shortcut, typically becomes fly-over
                help.

    icon:       An optional path to an .ico file to use as the icon for this
                shortcut.

    id:         On Linux, the id is used for the name of the '.desktop' file.

    name:       The display name for this shortcut.

    terminal:   A boolean value representing whether the shortcut should
                run within a shell / terminal.
    """
    if sys.platform == 'linux2':
        from linux2 import Menu, ShortCut

    elif sys.platform == 'darwin':
        from darwin import Menu, ShortCut

    elif sys.platform == 'win32':
        from win32 import Menu, ShortCut

    m = Menu(menu_name)
    if remove:
        for sc in shortcuts:
            ShortCut(m, sc).remove()
        m.remove()
    else:
        m.create()
        for sc in shortcuts:
            ShortCut(m, sc).create()


def transform_shortcut(dat_dir, sc):
    """
    Transform the shortcuts relative paths to absolute paths.
    """
    # Make the path to the executable absolute
    bin = sc['cmd'][0]
    if bin.startswith('..'):
        bin = abspath(join(dat_dir, bin))
    elif not bin.startswith('{{'):
        bin = join(sys.prefix, bin_dir_name, bin)
    sc['cmd'][0] = bin

    if (sys.platform == 'win32' and sc['terminal'] is False and
             not bin.startswith('{{') and isfile(bin + '-script.py')):
        argv = [join(sys.prefix, 'pythonw.exe'), bin + '-script.py']
        argv.extend(sc['cmd'][1:])
        sc['cmd'] = argv

    # Make the path of to icon files absolute
    for kw in ('icon', 'icns'):
        if kw in sc:
            sc[kw] = abspath(join(dat_dir, sc[kw]))


def get_shortcuts(dat_path):
    """
    reads and parses the appinst data file and returns the shortcuts
    """
    d = {}
    execfile(dat_path, d)

    shortcuts = d['SHORTCUTS']
    for sc in shortcuts:
        transform_shortcut(dirname(dat_path), sc)
    return shortcuts


def install_from_dat(dat_path):
    """
    Does a complete install given a data file.
    For an example see examples/appinst.dat.
    """
    dispatched_install(get_shortcuts(dat_path), remove=False)


def uninstall_from_dat(dat_path):
    """
    Uninstalls all items in a data file.
    """
    dispatched_install(get_shortcuts(dat_path), remove=True)
