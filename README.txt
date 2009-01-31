# Copyright (c) 2008 by Enthought, Inc.
# All rights reserved.

AppInst
=======

NOTE:
    This package was developed by Enthought.  The name AppInst is
    a rename of what used to be called 'wininst'.


AppInst's application_menus.py module can be used to install application menus,
as defined by the data structures documented in that module, to a number of
platforms.  RH3 and RH4 for both KDE and Gnome has been tested.  The RH4
implementation conforms to FreeDesktop.org's Desktop Menu Standard (see
http://standards.freedesktop.org/menu-spec/1.0/), and thus may likely work on
many Linux distributions.  However, minor modifications to the application_menus
module within this source may be necessary to get it to try that mechanism on
anything but RH4.

AppInst's common.py module simply exposes the api used in python's bdist_wininst
built executables.  The majority of the code is from Python's source, just
exposed as a python extension so it can be used for post-install steps by
various installation tools, like the Enstaller app among other things.  This
extension probably needs to be built with a Microsoft compiler.

