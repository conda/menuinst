# Copyright (c) 2008 by Enthought, Inc.
# All rights reserved.


import os


def filesystem_escape(name):
    """
    Replace special chars in a name to make it compatible with filesystem
    restrictions.

    """

    # Replace spaces, periods, and parenthesis with underscores.
    result = name.replace(' ', '_').replace('.', '_').replace('(', '_'). \
        replace(')', '_')

    return result


def make_desktop_entry(type, name, comment, exe, terminal, location,
    filename=None, categories=None, icon=None):
    """
    Create a desktop entry that conforms to the format of the Desktop Entry
    Specification by freedesktop.org.  See:
            http://freedesktop.org/Standards/desktop-entry-spec

    An entry is a .desktop file that includes the application's type,
    executable, name, etc.   It will be placed in the specified location with
    the specified filename.  If a filename isn't specified, then one is created
    by "escaping" the entry name.  Note that the filename should NOT include
    the '.desktop' extension.

    """

    # Build the text to go within the .desktop file.
    entry_code = """[Desktop Entry]
Type=%s
Encoding=UTF-8
Name=%s
Comment=%s
Exec=%s
Terminal=%s
""" % (type, name, comment, exe, terminal)
    if categories is not None:
        entry_code = entry_code + 'Categories=%s\n' % categories
    if icon is not None:
        entry_code = entry_code + "Icon=%s\n" % icon

    # Ensure we have a filename for the .desktop file.
    if filename is None:
        filename = filesystem_escape(name)
    filename = os.path.join(location, '%s.desktop' % filename)

    # Create the desktop entry file.
    f = open(filename, "w")
    f.write(entry_code)
    f.close()

    return


def make_directory_entry(name, comment, location, filename=None, icon=None):
    """
    Create a directory entry for KDE or Gnome2.

    """

    # Build the text to go within the .directory file.
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

    # Ensure we have a filepath for the .directory file.
    if filename is None:
        filename = filesystem_escape(name)
    filename = os.path.join(location, '%s.directory' % filename)

    # Create the desktop entry file.
    f = open(filename, "w")
    f.write(entry_code)
    f.close()

    return

