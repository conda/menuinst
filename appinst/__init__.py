# Copyright (c) 2008-2011 by Enthought, Inc.
# Copyright (c) 2013 Continuum Analytics, Inc.
# All rights reserved.

import sys
import json


if sys.platform.startswith('linux'):
    from linux import Menu, ShortCut

elif sys.platform == 'darwin':
    from darwin import Menu, ShortCut

elif sys.platform == 'win32':
    from win32 import Menu, ShortCut



def install(path, remove=False, prefix=sys.prefix):
    """
    install Menu and shortcuts
    """
    shortcuts = json.load(open(path))

    m = Menu('Python-%i.%i' % sys.version_info[:2])
    if remove:
        for sc in shortcuts:
            ShortCut(m, sc, prefix=prefix).remove()
        m.remove()
    else:
        m.create()
        for sc in shortcuts:
            ShortCut(m, sc, prefix=prefix).create()
