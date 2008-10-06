# Copyright (c) 2008 by Enthought, Inc.
# All rights reserved.


import os
import platform
import sys
import warnings

from appinst.shortcuts.shortcut_creation_error import ShortcutCreationError
from appinst.shortcuts.util import make_desktop_entry, make_directory_entry


# Determine our platform and version.
PLAT, PVER = platform.dist()[:2]
if PLAT.lower().startswith('redhat'):
    PLAT = 'rhel'
    if len(PVER) and PVER[0] in ['3', '4', '5']:
        PVER = PVER[0]

# Define shortcut methods based on the platform.
if PLAT=='rhel' and PVER=='3':
    from appinst.shortcuts.rh3 import (user_gnome, user_kde, system_gnome,
        system_kde)
elif PLAT == 'rhel' and PYVER == '4':
    from appinst.shortcuts.rh4 import (user_gnome, user_kde, system_gnome,
        system_kde)
else:
    warnings.warn('Unknown platform (%s) and version (%s). Unable '
        'to create shortcuts.' % (PLAT, PVER))
    def dummy(callback):
        return
    user_gnome = user_kde = system_gnome = system_kde = dummy


def _add_menu_links(enthought_dir, desktop):
    """
    Create the application links needed by EPD.

    This function documents the desired layout of the Enthought menu created
    by EPD.   It is used by both KDE and Gnome2.

    """

    if desktop=="kde":
       file_browser = "kfmclient openURL"
    if desktop=='gnome2':
       file_browser = "nautilus"

    # PyLab (IPython)
    bin_dir = os.path.join(sys.prefix, "bin")
    make_desktop_entry(type='Application', name='PyLab (IPython)',
        comment='PyLab in an IPython shell',
        exe=os.path.join(bin_dir, "ipython") + " -pylab", terminal='true',
        menu_dir=enthought_dir)

    # Mayavi
    make_desktop_entry(type='Application', name='Mayavi',
        comment='Envisage plugin for 3D visualization',
        exe=os.path.join(bin_dir, "mayavi2"), terminal='false',
        menu_dir=enthought_dir)

    # Documentation
    docs_dir = os.path.join(sys.prefix, "Docs")
    import webbrowser
    docs_exe = "%s %s " % (webbrowser.get().name, os.path.join(docs_dir,
        "index.html"))
    make_desktop_entry(type='Application', name='Documentation (HTML)',
        comment='EPD Documentation', exe=docs_exe, terminal='false',
        menu_dir=enthought_dir)

    # Examples
    examples_dir = os.path.join(sys.prefix, "Examples")
    examples_folder = os.path.join(enthought_dir, 'Examples')
    if not os.path.exists(examples_folder):
        os.mkdir(examples_folder)
    for dir in os.listdir(examples_dir):
        make_desktop_entry(type='Application', name=dir, comment=dir,
            exe="%s %s" % (file_browser, os.path.join(examples_dir, dir)),
            terminal='false', menu_dir=examples_folder,
            categories="Enthought;Examples;")

    return


def create_shortcuts(install_mode='user'):
    """
    Creates application shortcuts for an installation.

    Shortcuts will be created for both Gnome and KDE if they're both available.

    install_mode: should be either 'user' or 'system'.

    """

    if install_mode != 'user' and install_mode != 'system':
        warnings.warn('Unknown install mode.  Must be either "user" or '
            '"system" but got "%s"' % install_mode)
        return

    # Try installing KDE shortcuts.
    try:
        if install_mode == 'user':
            user_kde(_add_menu_links)
        else:
            system_kde(_add_menu_links)
    except ShortcutCreationError, ex:
        print >>sys.stderr, ex.message

    # Try a Gnome install
    try:
        if install_mode == 'user':
            user_gnome(_add_menu_links)
        else:
            system_gnome(_add_menu_links)
    except ShortcutCreationError, ex:
        print >>sys.stderr, ex.message


if __name__ == "__main__":
    create_shortcuts()
