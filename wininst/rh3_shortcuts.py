# Copyright (c) 2008 by Enthought, Inc.
# All rights reserved.


import os
from os import path
import shutil
import sys
from xml.etree import ElementTree

#############################################################################
# Create shortcut method
#############################################################################

def create_shortcuts(install_mode='user'):
    """ Creates shortcuts for User Gnome and KDE desktop menus
        install_mode: should be 'user' or 'system'
    """
    
    if install_mode != 'user' and install_mode != 'system':
        return
    
    if install_mode == 'user':
        kde_shortcut_method = create_user_kde_shortcuts
        gnome_shortcut_method = create_user_gnome_shortcuts
    else:
        kde_shortcut_method = create_system_kde_shortcuts
        gnome_shortcut_method = create_system_gnome_shortcuts
        
    try:
        kde_shortcut_method()
    except ShortcutCreationError, ex:
        print >>sys.stderr, ex.message
    
    try:
        gnome_shortcut_method()
    except ShortcutCreationError, ex:
        print >>sys.stderr, ex.message
    
#############################################################################
# Helper classes and methods
#############################################################################

class ShortcutCreationError(Exception):
    pass
    
def add_menu_links(enthought_dir, desktop):
    if desktop=="kde":
       file_browser = "kfmclient openURL"
    if desktop=='gnome2':
       file_browser = "nautilus"



    # Add menu links
    bin_dir = path.join(sys.prefix, "bin")
    docs_dir = path.join(sys.prefix, "Docs")
    examples_dir = path.join(sys.prefix, "Examples")

    # PyLab (IPython)
    make_desktop_entry(type='Application', name='PyLab (IPython)', \
        comment='PyLab in an IPython shell', \
        exe=path.join(bin_dir, "ipython") + " -pylab", terminal='true', \
        menu_dir=enthought_dir)

    # Mayavi
    make_desktop_entry(type='Application', name='Mayavi', \
        comment='Envisage plugin for 3D visualization', \
        exe=path.join(bin_dir, "mayavi2"), terminal='false', \
        menu_dir=enthought_dir)

    # Documentation (HTML)
    import webbrowser
    make_desktop_entry(type='Application', name='Documentation (HTML)',
        comment='EPD Documentation',
        exe="%s %s " %(webbrowser.get().name, path.join(docs_dir, "index.html")), 
        terminal='false',
        menu_dir=enthought_dir)
    
    # Demo directory menu links
    demos_menu_dir = path.join(enthought_dir, 'Demos')

    if not path.exists(demos_menu_dir):
        os.mkdir(demos_menu_dir)

    demos = {'traits' : 'Traits',
            'chaco2' : 'Chaco (2D plotting)',
            'envisage' :'Envisage (Pluggable Applications)',
            'mayavi' : 'Mayavi (3D visualization)', 
            'tvtk' : 'TVTK (Traits-VTK)',
            'enable2' : 'Enable (Drawing Components)', 
            'kiva' : 'Kiva (2D Drawing)'
            }
            
    for key,value in demos.items():
        make_desktop_entry(type='Application', name=value, comment=value, \
            exe="%s %s" % (file_browser, path.join(examples_dir, key)), terminal='false', \
            menu_dir=demos_menu_dir, categories="Enthought;Demo;" ) 

# Create a .desktop file given the application type, executable, name, etc...
# and the directory in which to create it.
def make_desktop_entry( type, name, comment, exe, terminal, 
                        menu_dir, categories='Enthought'):
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
    filename = path.join(menu_dir, '%s.desktop' % filename)
    f = open(filename, "w")
    f.write(entry_code)
    f.close()

def make_directory_entry(name, comment, menu_dir):
    entry_code = """[Desktop Entry]
Name=%s
Comment=%s
Icon=
Encoding=UTF-8
Type=Directory
""" % (name, comment)

    # Create the desktop entry file.
    filename = path.join(menu_dir, '%s.directory' % name.split(" ")[0])
    f = open(filename, "w")
    f.write(entry_code)
    f.close()

#############################################################################
# KDE-specific methods
#############################################################################

def _create_kde_shortcuts(kde_share_dir):
    """ Given a kde-share-directory, create KDE shortcuts.
    """
    
    if not path.exists(kde_share_dir):
        raise ShortcutCreationError('No %s directory found' % kde_share_dir)
    
    # Find applnk directory.
    applnk_dir = None
    for dir in os.listdir(kde_share_dir):
        if dir.startswith("applnk"):
            applnk_dir = path.join(kde_share_dir, dir)


    if applnk_dir is None:
        raise ShortcutCreationError('Cannot find KDE applnk directory')
    
    enthought_dir = path.join(applnk_dir, "Enthought")

    if not path.exists(enthought_dir):
        os.mkdir(enthought_dir)

    add_menu_links(enthought_dir, "kde")
    
    # Force the menus to refresh.
    os.system("kbuildsycoca")
            
def create_system_kde_shortcuts():
    """ Creates the sytem KDE shortcuts
    """
    _create_kde_shortcuts('/usr/share')
    
def create_user_kde_shortcuts():
    """ Creates the user KDE shortcuts
    """
    home_dir = path.expanduser("~")
    kde_dir = path.join(home_dir, ".kde")
    kde_share_dir = path.join(kde_dir, 'share')

    # Check if the user uses KDE by checking if the 
    # .kde and .kde/share dirs exists
    
    if not path.exists(kde_dir):
        raise ShortcutCreationError('No user .kde directory found')

    _create_kde_shortcuts(kde_share_dir)

#############################################################################
# Gnome2-specific methods
#############################################################################

def _create_gnome_shortcuts(vfolder_dir, apps_vfolder):
    """ Given the location to place .directory files, and the configuration 
        file that has to be modified, create shortcuts in Gnome2.
        
        vfolder_dir: Location to place .directory files
        apps_vfolder: Configuration file; either applications.menu or 
                      applications.vfolder-info file
    """
    
    app_vfolder_tree = ElementTree.parse(apps_vfolder)
    app_vfolder_root = app_vfolder_tree.getroot()
    
    # Look for previous Enthought MergeDirs and remove them
    enthought_vfolder_dir = path.abspath(path.join(vfolder_dir, 'Enthought'))
    for element in app_vfolder_root.findall('MergeDir'):
        if element.text == enthought_vfolder_dir:
            app_vfolder_root.getchildren().remove(element)
    
    # Add the MergeDir
    merge_dir_element = ElementTree.SubElement(app_vfolder_root, 'MergeDir')
    merge_dir_element.text = path.abspath(enthought_vfolder_dir)
    
    # Find the Applications Folder to put Enthought under
    applications_folder_element = None
    for element in app_vfolder_root.findall('Folder'):
        if element.find('Name').text == 'Applications':
            applications_folder_element = element
            break
        
    if applications_folder_element is None:
        raise ShortcutCreationMenu('Cannot find Gnome applications menu')
    
    # Look for previous Enthought folders and remove them
    for element in applications_folder_element.findall('Folder'):
        if element.find('Name').text == 'Enthought':
            applications_folder_element.getchildren().remove(element)
            break
    
    # Add the Enthought Folder
    enthought_dir_element = ElementTree.SubElement(applications_folder_element, 'Folder')
    ElementTree.SubElement(enthought_dir_element, 'Name').text = 'Enthought'
    ElementTree.SubElement(enthought_dir_element, 'Directory').text = 'Enthought.directory'
    query_element = ElementTree.SubElement(enthought_dir_element, 'Query')
    and_element = ElementTree.SubElement(query_element, 'And')
    ElementTree.SubElement(and_element, 'Keyword').text = 'Enthought'
    not_element = ElementTree.SubElement(and_element, 'Not')
    ElementTree.SubElement(not_element, 'Keyword').text = 'Demo'

    # Add the demo sub-menu
    demo_dir_element = ElementTree.SubElement(enthought_dir_element, 'Folder')
    ElementTree.SubElement(demo_dir_element, 'Name').text = 'Demos'
    ElementTree.SubElement(demo_dir_element, 'Directory').text = 'Enthought-demos.directory'
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
    if not path.exists(enthought_vfolder_dir):
        os.mkdir(enthought_vfolder_dir)
    
    add_menu_links(enthought_vfolder_dir, "gnome2")
    

def create_system_gnome_shortcuts():
    """ Create the system Gnome2 shortcuts
    """
    vfolder_dir = '/usr/share/desktop-menu-files'
    apps_vfolder = '/etc/X11/desktop-menus/applications.menu'
    if not path.exists(vfolder_dir):
        raise ShortcutCreationError('Could not find %s' % vfolder_dir)
    if not path.exists(apps_vfolder):
        raise ShortcutCreationError('Could not find %s' % apps_vfolder)
    _create_gnome_shortcuts(vfolder_dir, apps_vfolder)
    
def create_user_gnome_shortcuts():
    """ Creates the user Gnome2 shortcuts
    """
    home_dir = path.expanduser("~")
    gnome_dir = path.join(home_dir, ".gnome2")
    vfolder_dir = path.join(gnome_dir, "vfolders")
    
    if not path.exists(gnome_dir):
        raise ShortcutCreationError('No user .gnome2 directory found')
    
    if not path.exists(vfolder_dir):
        os.mkdir(vfolder_dir)
        
    user_apps_vfolder = path.join(vfolder_dir, 'applications.vfolder-info')
    sys_apps_vfolder = path.join('/', 'etc', 'X11', 'desktop-menus', 'applications.menu')
    
    if not path.exists(sys_apps_vfolder):
        raise ShortcutCreationError('Cannot find system "applications.menu" file')
    
    if not path.exists(user_apps_vfolder):
        shutil.copyfile(sys_apps_vfolder, user_apps_vfolder)
    
    _create_gnome_shortcuts(vfolder_dir, user_apps_vfolder)
    


if __name__ == "__main__":
    create_shortcuts()
