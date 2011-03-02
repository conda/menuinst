# Copyright (c) 2008-2011 by Enthought, Inc.
# All rights reserved.

import sys
import platform
from os.path import abspath, dirname, isfile, join

from egginst.utils import bin_dir_name

# The custom_tools package is importable when the Python was created by an
# "enicab" installer, in which case the directory custom_tools contains
# platform-independent install information in __init__.py and platform-specific
# information about user setting chosen during the install process.
try:
    import custom_tools
    menu = custom_tools.FULL_NAME
except ImportError:
    menu = 'Python-%i.%i' % sys.version_info[:2]


def install(shortcuts, uninstall=False):
    """
    Install an application shortcut according to the specified mode.

    This call is meant to work on all platforms.  If done on Linux, the menu
    will be installed to both Gnome and KDE desktops if they are available.

    Note that the information required is sufficient to install application
    menus on systems that follow the format of the Desktop Entry Specification
    by freedesktop.org.  See:
            http://freedesktop.org/Standards/desktop-entry-spec

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
                is used as the id.
            name: The display name for this shortcut.
            terminal: A boolean value representing whether the shortcut should
                run within a shell / terminal.
    """
    #import pprint
    #pp = pprint.PrettyPrinter(indent=4, width=20)
    #print 'SHORTCUTS: %s' % pp.pformat(shortcuts)
    if sys.platform == 'linux2':
        dist = platform.dist()
        if dist[0] == 'redhat' and dist[1].startswith('3'):
            from rh3 import install
        elif dist[0] == 'redhat' and dist[1].startswith('4'):
            from rh4 import install
        else:
            from linux2 import install

    elif sys.platform == 'darwin':
        from osx import install

    elif sys.platform == 'win32':
        from win32 import install

    else:
        print 'Unhandled platform. Unable to create application menu(s).'

    install(menu, shortcuts, uninstall=uninstall)


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


def transform(path):
    """
    reads and parses the appinst data file and returns the shortcuts
    """
    d = {}
    execfile(path, d)

    shortcuts = d['SHORTCUTS']
    for sc in shortcuts:
        transform_shortcut(dirname(path), sc)
    return shortcuts


def install_from_dat(path):
    """
    Does a complete install given a data file.
    For an example see examples/appinst.dat.
    """
    install(transform(path))


def uninstall_from_dat(path):
    """
    Uninstalls all items in a data file.
    """
    if sys.platform != 'win32':
        # FIXME:
        # Once time allows, we want the uninstall also to work on
        # Unix platforms.
        return
    install(transform(path), uninstall=True)
