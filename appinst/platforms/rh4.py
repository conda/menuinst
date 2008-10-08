# Copyright (c) 2008 by Enthought, Inc.
# All rights reserved.


import os
import shutil
import sys
from xml.etree import ElementTree

from appinst.shortcuts.shortcut_creation_error import ShortcutCreationError
from appinst.shortcuts.util import make_directory_entry


def _add_menu_links(menus, shortcuts, enthought_dir, desktop):
    """
    Create the application links needed by EPD.

    This function creates application short-cuts for the desired layout of the
    Enthought menu in EPD.  It assumes that application short-cuts follow the
    format of the Desktop Entry Specification by freedesktop.org.  See:
        http://freedesktop.org/Standards/desktop-entry-spec

    """

    if desktop=="kde":
       file_browser = "kfmclient openURL"
    if desktop=='gnome2':
       file_browser = "nautilus"

    # PyLab (IPython)
    bin_dir = os.path.join(sys.prefix, "bin")
    make_desktop_entry(type='Application', name='PyLab (IPython)',
        comment='PyLab in an IPython shell',
        exe=os.path.join(bin_dir, "ipython") + " -pylab", terminal='true',
        menu_dir=enthought_dir)

    # Mayavi
    make_desktop_entry(type='Application', name='Mayavi',
        comment='Envisage plugin for 3D visualization',
        exe=os.path.join(bin_dir, "mayavi2"), terminal='false',
        menu_dir=enthought_dir)

    # Documentation
    docs_dir = os.path.join(sys.prefix, "Docs")
    import webbrowser
    docs_exe = "%s %s " % (webbrowser.get().name, os.path.join(docs_dir,
        "index.html"))
    make_desktop_entry(type='Application', name='Documentation (HTML)',
        comment='EPD Documentation', exe=docs_exe, terminal='false',
        menu_dir=enthought_dir)

    # Examples
    examples_dir = os.path.join(sys.prefix, "Examples")
    examples_folder = os.path.join(enthought_dir, 'Examples')
    if not os.path.exists(examples_folder):
        os.mkdir(examples_folder)
    for dir in os.listdir(examples_dir):
        make_desktop_entry(type='Application', name=dir, comment=dir,
            exe="%s %s" % (file_browser, os.path.join(examples_dir, dir)),
            terminal='false', menu_dir=examples_folder,
            categories="Enthought;Examples;")

    return



#############################################################################
# KDE-specific methods
#############################################################################

def _create_kde_shortcuts(share_dir, callback):
    """
    Create KDE shortcuts in the specified share dir.

    The specified callback is called once we know what directory to create
    links within.

    """

    # Safety check to ensure the share dir actually exists.
    if not os.path.exists(share_dir):
        raise ShortcutCreationError('No %s directory found' % share_dir)

    # Find applnk directory.
    # FIXME: We should be using the 'kde-config' command to find either the
    # paths where it looks for 'apps' resources (i.e. kde-config --path apps)
    # or to get the prefix to install resource files to.
    # (i.e. kde-config --install apps)
    applnk_dir = None
    for dir in os.listdir(share_dir):
        if dir.startswith("applnk"):
            applnk_dir = os.path.join(share_dir, dir)
    if applnk_dir is None:
        raise ShortcutCreationError('Cannot find KDE applnk directory')

    # Ensure a top-level Enthought folder exists, then create the menu links
    # in it by calling the callback method.
    enthought_dir = os.path.join(applnk_dir, "Enthought")
    if not os.path.exists(enthought_dir):
        os.mkdir(enthought_dir)
    callback(enthought_dir, 'kde')

    # Force the menus to refresh.
    os.system('kbuildsycoca')

    return


def system_kde(callback):
    """
    Creates the sytem KDE shortcuts

    The specified callback is called once we know what directory to create
    links within.

    """

    _create_kde_shortcuts('/usr/share', callback)

    return


def user_kde(callback):
    """
    Creates the user KDE shortcuts

    The specified callback is called once we know what directory to create
    links within.

    """

    # Check if the user uses KDE by checking if the '.kde/share' dir exists
    share_dir = os.path.abspath(os.path.join(os.path.expanduser('~'), '.kde',
        'share'))
    if not os.path.exists(share_dir):
        raise ShortcutCreationError('No user .kde directory found')

    # Create our shortcuts under the share dir.
    _create_kde_shortcuts(share_dir, callback)

    return


#############################################################################
# Gnome2-specific methods
#############################################################################

def _create_gnome_shortcuts(vfolder_dir, apps_vfolder, callback):
    """
    Create Gnome2 shortcuts in the specified location.

    The specified callback is called once we know what directory to create
    links within.

    vfolder_dir: Location to place .directory files
    apps_vfolder: Configuration file; either applications.menu or
        applications.vfolder-info file
    """

    app_vfolder_tree = ElementTree.parse(apps_vfolder)
    app_vfolder_root = app_vfolder_tree.getroot()

    # Create MergeDirs but only after we clean up from any previous install by
    # deleteing existing MergeDirs.
    enthought_vfolder_dir = os.path.abspath(os.path.join(vfolder_dir,
        'Enthought'))
    for element in app_vfolder_root.findall('MergeDir'):
        if element.text == enthought_vfolder_dir:
            app_vfolder_root.getchildren().remove(element)
    merge_dir_element = ElementTree.SubElement(app_vfolder_root, 'MergeDir')
    merge_dir_element.text = os.path.abspath(enthought_vfolder_dir)

    # Find the location for the Enthought folder.   Clean out any previous
    # content there.
    applications_folder_element = None
    for element in app_vfolder_root.findall('Folder'):
        if element.find('Name').text == 'Applications':
            applications_folder_element = element
            break
    if applications_folder_element is None:
        raise ShortcutCreationMenu('Cannot find Gnome applications menu')
    for element in applications_folder_element.findall('Folder'):
        if element.find('Name').text == 'Enthought':
            applications_folder_element.getchildren().remove(element)
            break

    # Add the Enthought Folder
    enthought_dir_element = ElementTree.SubElement(applications_folder_element,
        'Folder')
    ElementTree.SubElement(enthought_dir_element, 'Name').text = 'Enthought'
    ElementTree.SubElement(enthought_dir_element, 'Directory').text = \
        'Enthought.directory'
    query_element = ElementTree.SubElement(enthought_dir_element, 'Query')
    and_element = ElementTree.SubElement(query_element, 'And')
    ElementTree.SubElement(and_element, 'Keyword').text = 'Enthought'
    not_element = ElementTree.SubElement(and_element, 'Not')
    ElementTree.SubElement(not_element, 'Keyword').text = 'Demo'

    # Add the demo sub-menu
    demo_dir_element = ElementTree.SubElement(enthought_dir_element, 'Folder')
    ElementTree.SubElement(demo_dir_element, 'Name').text = 'Demos'
    ElementTree.SubElement(demo_dir_element, 'Directory').text = \
        'Enthought-demos.directory'
    query_element = ElementTree.SubElement(demo_dir_element, 'Query')
    and_element = ElementTree.SubElement(query_element, 'And')
    ElementTree.SubElement(and_element, 'Keyword').text = 'Enthought'
    ElementTree.SubElement(and_element, 'Keyword').text = 'Demo'

    # We are done with the vfolder, write it back out
    app_vfolder_tree.write(apps_vfolder)

    # make the .directory files
    make_directory_entry("Enthought", "", vfolder_dir)
    make_directory_entry("Enthought-demos", "", vfolder_dir)

    # make the .desktop files in the new directory
    if not os.path.exists(enthought_vfolder_dir):
        os.mkdir(enthought_vfolder_dir)

    callback(enthought_vfolder_dir, "gnome2")

    return


def system_gnome(callback):
    """
    Creates the sytem Gnome2 shortcuts

    The specified callback is called once we know what directory to create
    links within.

    """

    # Ensure the folder directory exists.
    vfolder_dir = '/usr/share/desktop-menu-files'
    if not os.path.exists(vfolder_dir):
        raise ShortcutCreationError('Could not find %s' % vfolder_dir)

    # Ensure the applications menu exists.
    apps_vfolder = '/etc/X11/desktop-menus/applications.menu'
    if not os.path.exists(apps_vfolder):
        raise ShortcutCreationError('Could not find %s' % apps_vfolder)

    # Create the shortcuts.
    _create_gnome_shortcuts(vfolder_dir, apps_vfolder, callback)

    return


def user_gnome(callback):
    """
    Creates the user Gnome2 shortcuts

    The specified callback is called once we know what directory to create
    links within.

    """

    # Check if the user uses Gnome by checking if the '.gnome2' dir exists
    gnome_dir = os.path.abspath(os.path.join(os.path.expanduser("~"),
        ".gnome2"))
    if not os.path.exists(gnome_dir):
        raise ShortcutCreationError('No user .gnome2 directory found')

    # Make sure a folders directory exists.
    vfolder_dir = os.path.join(gnome_dir, "vfolders")
    if not os.path.exists(vfolder_dir):
        os.mkdir(vfolder_dir)

    # Ensure an application folder exists, creating one if it didn't already
    # exist.
    apps_vfolder = os.path.join(vfolder_dir, 'applications.vfolder-info')
    if not os.path.exists(apps_vfolder):
        sys_apps_vfolder = '/etc/X11/desktop-menus/applications.menu'
        if not os.path.exists(sys_apps_vfolder):
            raise ShortcutCreationError('Cannot find template '
            '"applications.menu" file to create user apps folder from.')
        shutil.copyfile(sys_apps_vfolder, apps_vfolder)

    # Create the shortcuts.
    _create_gnome_shortcuts(vfolder_dir, apps_vfolder, callback)

    return



if __name__ == "__main__":
    create_shortcuts()
