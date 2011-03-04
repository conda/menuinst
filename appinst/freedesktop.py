# Copyright (c) 2008-2011 by Enthought, Inc.
# All rights reserved.

from os.path import join


def filesystem_escape(s):
    for c in ' ()':
        s = s.replace(c, '_')
    return s


def make_desktop_entry(d):
    """
    Create a desktop entry that conforms to the format of the Desktop Entry
    Specification by freedesktop.org.  See:
            http://freedesktop.org/Standards/desktop-entry-spec
    These should work for both KDE and Gnome2

    An entry is a .desktop file that includes the application's type,
    executable, name, etc.   It will be placed in the location specified within
    the passed dict.  The filename will be based on the ID specified within the
    dict.

    The following document the keys and values expected in the passed
    dictionary:
        categories:: string, short-cut should be displayed under.
        cmd:: list of strings: The executable command for this shortcut and any
            necessary arguments.
        comment:: string, optional: A comment about the shortcut.  Some systems
            may display this as a flyover.
        icon:: string, optional: The path to an icon file used to represent
            this shortcut.
        id:: string: The identifier used for this shortcut.  This becomes the
            filename.  It should NOT include the '.desktop'.
        location:: string: The directory in which to create the shortcut's
            '.desktop' file.  For safety, this should be an absolute path.
        name:: string: The display name for the shortcut.
        terminal:: boolean: Indicates whether the executable should be run
            within a shell.

    Returns the path to the entry file that was created.
    """
    # default values
    d.setdefault('comment', '')
    d.setdefault('icon', '')

    # Format the command to a single string.
    if isinstance(d['cmd'], list):
        d['cmd'] = ' '.join(d['cmd'])

    # Swap the terminal boolean to a string.
    if isinstance(d['terminal'], bool):
        d['terminal'] = str(d['terminal']).lower()

    ext = ('', 'KDE')[d['tp'] == 'kde']
    path = join(d['location'],
                '%s%s.desktop' % (filesystem_escape(d['id']), ext))
    fo = open(path, "w")

    # Build the basic text to go within the .desktop file.
    fo.write("""\
[Desktop Entry]
Type=Application
Encoding=UTF-8
Name=%(name)s
Comment=%(comment)s
Exec=%(cmd)s
Terminal=%(terminal)s
Icon=%(icon)s
Categories=%(categories)s
""" % d)

    if d['tp'] == 'kde':
        fo.write('OnlyShowIn=KDE\n')
    else:
        fo.write('NotShowIn=KDE\n')

    fo.close()

    return path


def make_directory_entry(d):
    """
    Create a directory entry that conforms to the format of the Desktop Entry
    Specification by freedesktop.org.  See:
            http://freedesktop.org/Standards/desktop-entry-spec
    These should work for both KDE and Gnome2

    An entry is a .directory file that includes the display name, icon, etc.
    It will be placed in the location specified within the passed dict.  The
    filename can be explicitly specified, but if not provided, will default to
    an escaped version of the name.

    The following document the keys and values expected in the passed
    dictionary:
        comment:: string, optional: A comment about this menu.  Some systems
            may display this as a flyover.
        icon:: string, optional: The path to an icon file used to represent
            this menu.
        location:: string: The directory in which to create this menu's
            '.directory' file.  For safety, this should be an absolute path.
        name:: string: The display name for the menu.
        type:: string, optional: The Type of the directory entry.  If not
            specified, 'Directory' will be used.

    Returns the path to the entry file that was created.
    """
    # default values
    d.setdefault('comment', '')
    d.setdefault('icon', '')

    fn = filesystem_escape(d['name'])
    path = join(d['location'], '%s.directory' % fn)

    fo = open(path, "w")
    fo.write("""\
[Desktop Entry]
Type=Directory
Encoding=UTF-8
Name=%(name)s
Comment=%(comment)s
Icon=%(icon)s
""" % d)
    fo.close()

    return path
