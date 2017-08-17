# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2013-2017 Continuum Analytics, Inc.
# Copyright (c) 2008-2011 by Enthought, Inc.
# All rights reserved.
#
# Licensed under the terms of the BSD 3-clause License (See LICENSE.txt)
# -----------------------------------------------------------------------------
"""Menuinst command line interface."""

# Standard library imports
import os
import sys

# Local imports
import menuinst


def main():
    from optparse import OptionParser

    p = OptionParser(
        usage="usage: %prog [options] MENU_FILE",
        description="install a menu item")

    p.add_option('-p', '--prefix',
                 action="store",
                 default=sys.prefix)

    p.add_option('--remove',
                 action="store_true")

    p.add_option('--version',
                 action="store_true")

    opts, args = p.parse_args()

    if opts.version:
        sys.stdout.write("menuinst: %s\n" % menuinst.__version__)
        return

    for arg in args:
        menuinst.install(os.path.join(opts.prefix, arg), opts.remove, opts.prefix)


if __name__ == '__main__':
    main()
