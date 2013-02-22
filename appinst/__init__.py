# Copyright (c) 2008-2011 by Enthought, Inc.
# Copyright (c) 2013 Continuum Analytics, Inc.
# All rights reserved.

import sys
from os.path import abspath, dirname, isfile, join

from utils import bin_dir_name

# The custom_tools package is importable when the Python was created by an
# "enicab" installer, in which case the directory custom_tools contains
# platform-independent install information in __init__.py and platform-specific
# information about user setting chosen during the install process.
try:
    import custom_tools
    menu_name = custom_tools.FULL_NAME
except ImportError:
    menu_name = 'Python-%i.%i' % sys.version_info[:2]


def install(shortcuts, remove, prefix=None):
    """
    install Menu and shortcuts
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
            ShortCut(m, sc, prefix=prefix).remove()
        m.remove()
    else:
        m.create()
        for sc in shortcuts:
            ShortCut(m, sc, prefix=prefix).create()


def transform_shortcut(dat_dir, sc, prefix=None):
    """
    transform the shortcuts relative paths to absolute paths
    """
    prefix = prefix if prefix is not None else sys.prefix
    # Make the path to the executable absolute
    bin = sc['cmd'][0]
    if bin.startswith('..'):
        bin = abspath(join(dat_dir, bin))
    elif not bin.startswith('{{'):
        bin = join(prefix, bin_dir_name, bin)
    sc['cmd'][0] = bin

    if (sys.platform == 'win32' and sc['terminal'] is False and
             not bin.startswith('{{') and isfile(bin + '-script.py')):
        argv = [join(prefix, 'pythonw.exe'), bin + '-script.py']
        argv.extend(sc['cmd'][1:])
        sc['cmd'] = argv

    # Make the path of to icon files absolute
    for kw in ('icon', 'icns'):
        if kw in sc:
            sc[kw] = abspath(join(dat_dir, sc[kw]))


def get_shortcuts(dat_path, prefix=None):
    """
    reads and parses the appinst data file and returns the shortcuts
    """
    d = {}
    execfile(dat_path, d)

    shortcuts = d['SHORTCUTS']
    for sc in shortcuts:
        transform_shortcut(dirname(dat_path), sc, prefix=prefix)
    return shortcuts


def install_from_dat(dat_path, prefix=None):
    """
    does a complete install given a data file, the prefix is the system prefix
    to use.
    """
    install(get_shortcuts(dat_path, prefix=prefix), remove=False, prefix=prefix)


def uninstall_from_dat(dat_path, prefix=None):
    """
    uninstalls all items in a data file, the prefix is the system prefix to
    use.
    """
    install(get_shortcuts(dat_path, prefix=prefix), remove=True, prefix=prefix)
