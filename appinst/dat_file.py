# Copyright (c) 2009 by Enthought, Inc.
# All rights reserved.
"""
This module provides an interface to appinst which allows installing
applications by specifying the path to a data file.  For an example of
such a data file see examples/appinst.dat, the example file contains
detailed comments about how this is done exactly.
"""

import sys
from os.path import abspath, dirname, isfile, join

from egginst.utils import bin_dir_name

from appinst.application_menus import install, uninstall



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
    Reads and parses the appinst data file and returns a tuple
    (menus, shortcuts) where menus and shortcuts are objects which
    the funtions install() and uninstall() in the application_menus
    module expects.
    """
    # default values
    d = {'MENUS': []}
    execfile(path, d)

    shortcuts = d['SHORTCUTS']
    for sc in shortcuts:
        transform_shortcut(dirname(path), sc)

    return d['MENUS'], shortcuts


def install_from_dat(path):
    """
    Does a complete install given a data file.
    For an example see examples/appinst.dat.
    """
    install(*transform(path))


def uninstall_from_dat(path):
    """
    Uninstalls all items in a data file.
    """
    if sys.platform != 'win32':
        # FIXME:
        # Once time allows, we want the uninstall also to work on
        # Unix platforms.
        return

    uninstall(*transform(path))
