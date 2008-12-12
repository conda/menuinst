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


def make_desktop_entry(dict):
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
    dict.setdefault('comment', '')
    dict.setdefault('encoding', 'UTF-8')
    dict.setdefault('icon', '')
    dict.setdefault('type', 'Application')

    # Format the command to a single string.
    if isinstance(dict['cmd'], list):
        dict['cmd'] = ' '.join(dict['cmd'])

    # Swap the terminal boolean to a string.
    if isinstance(dict['terminal'], bool):
        dict['terminal'] = str(dict['terminal']).lower()

    # Build the basic text to go within the .desktop file.
    entry_code = """[Desktop Entry]
Type=%(type)s
Encoding=%(encoding)s
Name=%(name)s
Comment=%(comment)s
Exec=%(cmd)s
Terminal=%(terminal)s
Icon=%(icon)s
""" % dict

    # Only add a categories line if categories were truely specified.
    if dict.has_key('categories') and len(dict['categories']) > 0:
        cats = dict['categories']
        if isinstance(cats, list):
            cats = ';'.join(cats)
        entry_code = entry_code + 'Categories=%s\n' % cats

    ext = ''
    if dict.has_key('only_show_in'):
        desktop = dict['only_show_in']
        entry_code = entry_code + 'OnlyShowIn=%s\n' % desktop
        ext = desktop
    elif dict.has_key('not_show_in'):
        desktop = dict['not_show_in']
        entry_code = entry_code + 'NotShowIn=%s\n' % desktop

    # Create the desktop entry file.
    path = os.path.join(dict['location'], '%s%s.desktop' % (filesystem_escape(dict['id']), ext))
    fh = open(path, "w")
    fh.write(entry_code)
    fh.close()

    return path


def make_directory_entry(dict):
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
    dict.setdefault('comment', '')
    dict.setdefault('encoding', 'UTF-8')
    dict.setdefault('icon', '')
    dict.setdefault('type', 'Directory')

    # Build the text to go within the .directory file.
    entry_code = """[Desktop Entry]
Type=%(type)s
Encoding=%(encoding)s
Name=%(name)s
Comment=%(comment)s
Icon=%(icon)s
""" % dict

    # Ensure we have a filename for the .directory file.
    filename = dict.get('filename', filesystem_escape(dict['name']))

    # Create the desktop entry file.
    path = os.path.join(dict['location'], '%s.directory' % filename)
    fh = open(path, "w")
    fh.write(entry_code)
    fh.close()

    return path

