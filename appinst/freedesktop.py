# Copyright (c) 2008-2009 by Enthought, Inc.
# All rights reserved.

from os.path import join


def filesystem_escape(s):
    """
    Replace special chars in a name to make it compatible with filesystem
    restrictions.
    """
    # Replace spaces, periods, and parenthesis with underscores.
    for c in ' .()':
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
        categories:: list of strings, optional: The list of categories this
            short-cut should be displayed under.
        cmd:: list of strings: The executable command for this shortcut and any
            necessary arguments.
        comment:: string, optional: A comment about the shortcut.  Some systems
            may display this as a flyover.
        encoding:: string, optional: The encoding for the display name.  If not
            specified, 'UTF-8' will be used.
        icon:: string, optional: The path to an icon file used to represent
            this shortcut.
        id:: string: The identifier used for this shortcut.  This becomes the
            filename.  It should NOT include the '.desktop'.
        location:: string: The directory in which to create the shortcut's
            '.desktop' file.  For safety, this should be an absolute path.
        name:: string: The display name for the shortcut.
        terminal:: boolean: Indicates whether the executable should be run
            within a shell.
        type:: string, optional: The Type of the shortcut.  If not specified,
            'Application' will be used.

    Returns the path to the entry file that was created.
    """

    # Ensure default values.
    d.setdefault('comment', '')
    d.setdefault('encoding', 'UTF-8')
    d.setdefault('icon', '')
    d.setdefault('type', 'Application')

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
    fo.write("""[Desktop Entry]
Type=%(type)s
Encoding=%(encoding)s
Name=%(name)s
Comment=%(comment)s
Exec=%(cmd)s
Terminal=%(terminal)s
Icon=%(icon)s
""" % d)
    cats = d['categories']
    if isinstance(cats, list):
        cats = ';'.join(cats)
    fo.write('Categories=%s\n' % cats)

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
        encoding:: string, optional: The encoding for the display name.  If not
            specified, 'UTF-8' will be used.
        filename:: string, optional: The name to use for the .directory file.
            If not specified, an escaped version of the 'name' will be used.
        icon:: string, optional: The path to an icon file used to represent
            this menu.
        location:: string: The directory in which to create this menu's
            '.directory' file.  For safety, this should be an absolute path.
        name:: string: The display name for the menu.
        type:: string, optional: The Type of the directory entry.  If not
            specified, 'Directory' will be used.

    Returns the path to the entry file that was created.
    """

    # Ensure default values.
    d.setdefault('comment', '')
    d.setdefault('encoding', 'UTF-8')
    d.setdefault('icon', '')
    d.setdefault('type', 'Directory')

    # Build the text to go within the .directory file.
    entry_code = """[Desktop Entry]
Type=%(type)s
Encoding=%(encoding)s
Name=%(name)s
Comment=%(comment)s
Icon=%(icon)s
""" % d

    # Ensure we have a filename for the .directory file.
    filename = d.get('filename', filesystem_escape(d['name']))

    # Create the desktop entry file.
    path = join(d['location'], '%s.directory' % filename)
    fo = open(path, "w")
    fo.write(entry_code)
    fo.close()

    return path
