# Copyright (c) 2009 by Enthought, Inc.
# All rights reserved.
import sys, os
import re
import shutil
from os.path import join, isdir, basename
from plistlib import Plist, writePlist


class Application(object):
    """
    Class for creating an application folder on OSX.  The application may
    be standalone executable, but more likely a Python script which is
    interpreted by the framework Python interpreter.
    """

    def __init__(self, name, script_path, icns_path=None,
                 apps_dir='/Applications', force=True, version='1.0.0'):
        """
        Required:
        ---------
        name         The name of the applications to be creating.

        script_path  Path to a python script which starts the application,
                     which will be copied to the correct location.

        Optional:
        ---------
        icns_path    Path to a .icns-file which contains the application
                     icon.  When not specified, the "Python rocket icon"
                     is copied from the Python framework.

        apps_dir     Directory in which the application folder will be created,
                     defaults to /Applications

        force        Remove an existing application with folder name if it
                     exists, defaults to True

        version      Version number of the application to be created
        """

        self.name = name
        self.version = version
        self.script_path = script_path
        self.version = version
        self.icns_path = icns_path
        self.apps_dir = apps_dir
        self.force = force

        self.app_dir = join(apps_dir, name + '.app')
        self.cont_dir = join(self.app_dir, 'Contents')
        self.rsrc_dir = join(self.cont_dir, 'Resources')
        self.macos_dir = join(self.cont_dir, 'MacOS')
        self.script_name = basename(script_path)

    def create(self):
        """
        Create the application.
        """
        self.create_dirs()
        self.write_pkginfo()
        self.write_icns()
        self.writePlistInfo()
        self.write_script()

    #=======================================================================
    # More os less private methods
    #=======================================================================

    def create_dirs(self):
        if self.force and isdir(self.app_dir):
            shutil.rmtree(self.app_dir)

        if isdir(self.app_dir):
            raise Exception("Application folder %r already exists" % root)

        os.makedirs(self.rsrc_dir)
        os.makedirs(self.macos_dir)

    def write_pkginfo(self):
        fo = open(join(self.cont_dir, 'PkgInfo'), 'w')
        fo.write(('APPL%s????' % self.name.replace(' ', ''))[:8])
        fo.close()

    def write_icns(self):
        if self.icns_path is None:
            # Try to get the default icon
            self.icns_path = join(sys.prefix, 'Resources/Python.app/Contents',
                             'Resources/PythonInterpreter.icns')
        
        shutil.copy(self.icns_path, self.rsrc_dir)

    def writePlistInfo(self):
        """
        Writes the Info.plist file in the Contests directory.
        """
        pl = Plist(
            CFBundleExecutable=self.script_name,
            CFBundleGetInfoString='%s-%s' % (self.name, self.version),
            CFBundleIconFile=basename(self.icns_path),
            CFBundleIdentifier='com.%s' % self.name,
            CFBundlePackageType='APPL',
            CFBundleVersion=self.version,
            CFBundleShortVersionString=self.version,
            )
        writePlist(pl, join(self.cont_dir, 'Info.plist'))

    def write_script(self):
        """
        Copies a python script (which starts the application) into the
        application folder (into Contests/MacOS) and makes sure the script
        uses sys.executable, which should be the "framework Python".
        """
        pat = re.compile(r'#!(.+)$', re.M)

        fi = open(self.script_path)
        data = fi.read()
        fi.close()

        path = join(self.macos_dir, self.script_name)
        fo = open(path, 'w')

        hashbang= '#!%s' % sys.executable
        if pat.match(data):
            fo.write(pat.sub(hashbang, data, count=1))
        else:
            fo.write(hashbang + '\n')
            fo.write(data)

        fo.close()
        os.chmod(path, 0755)


if __name__ == '__main__':
    # Example for testing:
    app = Application('Test Application', 'test123.py', apps_dir=os.getcwd())
    app.create()
