# Copyright (c) 2008 by Enthought, Inc.
# All rights reserved.


import os


def make_desktop_entry(type, name, comment, exe, terminal, location,
    categories='Enthought', icon=None):
    """
    Create an application entry for KDE or Gnome2.

    An application entry is a .desktop file that includes the application's
    type, executable, name, etc.   It will be placed in the specified location
    location.

    """

    entry_code = """[Desktop Entry]
Type=%s
Encoding=UTF-8
Name=%s
Comment=%s
Exec=%s
Terminal=%s
Categories=%s
""" % (type, name, comment, exe, terminal, categories)
    if icon is not None:
        entry_code = entry_code + "Icon=%s\n" % icon

    # Create the desktop entry file.
    filename = name.replace(' ', '')
    filename = filename.replace('(', '-').replace(')', '')
    filename = os.path.join(location, '%s.desktop' % filename)
    f = open(filename, "w")
    f.write(entry_code)
    f.close()

    return


def make_directory_entry(name, comment, location, icon=None):
    """
    Create a directory entry for KDE or Gnome2.

    """
    entry_code = """[Desktop Entry]
Type=Directory
Encoding=UTF-8
Name=%s
Comment=%s
""" % (name, comment)
    if icon is not None:
        entry_code = entry_code + "Icon=%s\n" % icon
    else:
        entry_code = entry_code + "Icon=\n"

    # Create the desktop entry file.
    filename = os.path.join(location, '%s.directory' % name.split(" ")[0])
    f = open(filename, "w")
    f.write(entry_code)
    f.close()

    return

