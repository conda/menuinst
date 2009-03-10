# Copyright (c) 2009 by Enthought, Inc.
# Author: Ilan Schnell

import sys
from os.path import abspath, dirname, join

from appinst.application_menus import install, uninstall

BIN_DIR = join(sys.prefix, 'Scripts' if sys.platform == 'win32' else 'bin')


def make_absolute(pkg_root, path):
    if pkg_root is None:
        # path is assumed to be absolute, so just return it
        return path

    path = shortcut[kw].replace('\\', '/')
    if path.startswith('/'):
        raise Exception("Assuming relative path, but %r starts with '/'" %
                        path)
    # make path absolute
    return join(pkg_root, join(*path.split('/')))


def change_shortcut(pkg_root, sc):
    # make the path to the executable absolute
    sc['cmd'][0] = join(BIN_DIR, sc['cmd'][0])

    # make the path of to icon files absolute
    for kw in ('icon', 'icns'):
        if kw in sc:
            sc[kw] = make_absolute(pkg_root, sc[kw])


def transform(path):
    """
    Reads and parses the appinst data file and returns a tuple
    (menus, shortcuts) where menus and shortcuts are objects which
    the funtions install() and uninstall() in the application_menus
    module expects.
    """
    # default values
    d = {'MENUS': [], 'PKG_ROOT' : 2}
    execfile(path, d)

    # pkg_root (not to be confused with d['PKG_ROOT']) is the absolute path
    # to the root of the package, or None in case relative paths are desired.
    if d['PKG_ROOT'] is None:
        pkg_root = None
    else:
        # The dirname of the appinst data file
        pkg_root = dirname(abspath(path))
        for i in xrange(d['pkg-root']):
            pkg_root = dirname(pkg_root)

    return (d['MENUS'], [change_shortcut(pkg_root, sc)
                         for sc in d['SHORTCUTS']])


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
