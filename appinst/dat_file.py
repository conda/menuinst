# Copyright (c) 2009 by Enthought, Inc.
# Author: Ilan Schnell

"""
This module provides an interface to appinst which allows installing
applications by specifying the path to a data file.  For an example of
such a data file see examples/appinst.dat, the example file contains
detailed comments about how this is done exactly.
"""


import sys
from os.path import abspath, dirname, join

from appinst.application_menus import install, uninstall


BIN_DIR = join(sys.prefix, 'Scripts' if sys.platform == 'win32' else 'bin')


def transform_shortcut(dat_dir, sc):
    """
    Given the directory the appinst data file is located in, fix some path.
    """
    # make the path to the executable absolute
    bin = sc['cmd'][0]
    if bin.startswith('..'):
        bin = abspath(join(dat_dir, bin))
    else:
        bin = join(BIN_DIR, bin)
    sc['cmd'][0] = bin

    # make the path of to icon files absolute
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
    given the path to an appinst data file, for an example see
    examples/appinst.dat, does an complete install.
    """
    install(*transform(path))


def uninstall_from_dat(path):
    """
    given the path to an appinst data file, uninstalls all items.
    """
    uninstall(*transform(path))
