# Copyright (c) 2009 by Enthought, Inc.
# All rights reserved.

import os
import shutil
import sys
from os.path import join, isdir, basename

from plistlib import Plist, writePlist


TERMINAL = '''\
#!/bin/sh
mypath="`dirname "$0"`"
osascript << EOF
tell application "System Events" to set terminalOn to (exists process "Terminal")
tell application "Terminal"
  if (terminalOn) then
    activate
    do script "\\"$mypath/startup.command\\"; exit"
  else
    do script "\\"$mypath/startup.command\\"; exit" in front window
  end if
end tell
EOF
exit 0
'''


class Application(object):
    """
    Class for creating an application folder on OSX.  The application may
    be standalone executable, but more likely a Python script which is
    interpreted by the framework Python interpreter.
    """

    def __init__(self, shortcut, force=True):
        """
        Required:
        ---------
        shortcut is a dictionary defining a shortcut per the AppInst standard.

        Optional:
        ---------
        force is a boolean indicating whether an existing application should
            be removed if it exists.  Defaults to True.
        """
        self.force = force

        # Store the required values out of the shortcut definition.
        self.args = shortcut['args']
        self.menu_dir = shortcut['menu_dir']
        self.name = shortcut['name']

        # Store some optional values out of the shortcut definition.
        self.icns_path = shortcut.get('icns', None)
        self.terminal = shortcut.get('terminal', False)
        self.version = shortcut.get('version', '1.0.0')

        # Calculate some derived values just once.
        self.app_dir = join(self.menu_dir, self.name + '.app')
        self.contents_dir = join(self.app_dir, 'Contents')
        self.resources_dir = join(self.contents_dir, 'Resources')
        self.macos_dir = join(self.contents_dir, 'MacOS')
        self.executable = self.name
        self.executable_path = join(self.macos_dir, self.executable)


    def create(self):
        """
        Create the application.
        """
        self._create_dirs()
        self._write_pkginfo()
        self._write_icns()
        self._writePlistInfo()
        self._write_script()


    #=======================================================================
    # Non-public methods
    #=======================================================================

    def _create_dirs(self):
        if self.force and isdir(self.app_dir):
            shutil.rmtree(self.app_dir)

        if isdir(self.app_dir):
            raise RuntimeError("Application bundle %r already exists" %
                               self.app_dir)

        # Only need to make leaf dirs as the 'makedirs' function creates the
        # rest on the way to the leaves.
        os.makedirs(self.resources_dir)
        os.makedirs(self.macos_dir)


    def _write_pkginfo(self):
        fo = open(join(self.contents_dir, 'PkgInfo'), 'w')
        fo.write(('APPL%s????' % self.name.replace(' ', ''))[:8])
        fo.close()


    def _write_icns(self):
        # Use a default icon if no icns file was specified.
        if self.icns_path is None:
            self.icns_path = join(sys.prefix, 'Resources/Python.app/Contents',
                                  'Resources/PythonInterpreter.icns')

        shutil.copy(self.icns_path, self.resources_dir)


    def _writePlistInfo(self):
        """
        Writes the Info.plist file in the Contests directory.
        """
        pl = Plist(
            CFBundleExecutable=self.executable,
            CFBundleGetInfoString='%s-%s' % (self.name, self.version),
            CFBundleIconFile=basename(self.icns_path),
            CFBundleIdentifier='com.%s' % self.name,
            CFBundlePackageType='APPL',
            CFBundleVersion=self.version,
            CFBundleShortVersionString=self.version,
            )
        writePlist(pl, join(self.contents_dir, 'Info.plist'))


    def _write_script(self):
        """
        Copies a python script (which starts the application) into the
        application folder (into Contests/MacOS) and makes sure the script
        uses sys.executable, which should be the "framework Python".
        """
        shell = "#!/bin/sh\n%s\n" % ' '.join(self.args)

        if self.terminal:
            path = join(self.macos_dir, 'startup.command')
            fo = open(path, 'w')
            fo.write(shell)
            fo.close()
            os.chmod(path, 0755)

            data = TERMINAL
        else:
            data = shell

        fo = open(self.executable_path, 'w')
        fo.write(data)
        fo.close()
        os.chmod(self.executable_path, 0755)


if __name__ == '__main__':
    # Example for testing:
    app = Application('Test Application', 'test123.py', apps_dir=os.getcwd())
    app.create()
