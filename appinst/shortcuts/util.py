# Copyright (c) 2008 by Enthought, Inc.
# All rights reserved.


import os


def make_desktop_entry(type, name, comment, exe, terminal, menu_dir,
    categories='Enthought'):
    """
    Create an application entry for KDE or Gnome2.

    An application entry is a .desktop file that includes the application's
    type, executable, name, etc.   It will be placed in the specified menu_dir
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

    # Create the desktop entry file.
    filename = name.replace(' ', '')
    filename = filename.replace('(', '-').replace(')', '')
    filename = os.path.join(menu_dir, '%s.desktop' % filename)
    f = open(filename, "w")
    f.write(entry_code)
    f.close()

    return


def make_directory_entry(name, comment, menu_dir):
    """
    Create a directory entry for KDE or Gnome2.

    """
    entry_code = """[Desktop Entry]
Name=%s
Comment=%s
Icon=
Encoding=UTF-8
Type=Directory
""" % (name, comment)

    # Create the desktop entry file.
    filename = os.path.join(menu_dir, '%s.directory' % name.split(" ")[0])
    f = open(filename, "w")
    f.write(entry_code)
    f.close()

    return

