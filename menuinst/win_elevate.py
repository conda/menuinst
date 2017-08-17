# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2013-2017 Continuum Analytics, Inc.
# Copyright (c) 2010 Preston Landers (Released under the Python 2.6.5 license)
# Copyright (c) 2008-2011 by Enthought, Inc.
# All rights reserved.
#
# Licensed under the terms of the BSD 3-clause License (See LICENSE.txt)
# -----------------------------------------------------------------------------
"""
See: http://stackoverflow.com/a/19719292/1170370 on 20160407 MCS.
"""

from __future__ import print_function

# Standard library imports
import sys
import os
import traceback


if sys.version_info < (3,):
    text_type = basestring
else:
    text_type = str


def isUserAdmin():
    if os.name == 'nt':
        import ctypes
        # WARNING: requires Windows XP SP2 or higher!
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            traceback.print_exc()
            print("Admin check failed, assuming not an admin.")
            return False
    elif os.name == 'posix':
        # Check for root on Posix
        return os.getuid() == 0
    else:
        raise RuntimeError("Unsupported operating system for this module: %s" % (os.name,))


def runAsAdmin(cmdLine=None, wait=True):
    if os.name != 'nt':
        raise RuntimeError("This function is only implemented on Windows.")

    import win32con, win32event, win32process
    from win32com.shell.shell import ShellExecuteEx
    from win32com.shell import shellcon

    python_exe = sys.executable

    if cmdLine is None:
        cmdLine = [python_exe] + sys.argv
    #elif type(cmdLine) not in (types.TupleType,types.ListType):
    elif not hasattr(cmdLine, "__iter__") or isinstance(cmdLine, text_type):
        raise ValueError("cmdLine is not a sequence.")
    cmd = '"%s"' % (cmdLine[0],)
    # XXX TODO: isn't there a function or something we can call to massage command line params?
    params = " ".join(['"%s"' % (x,) for x in cmdLine[1:]])
    # cmdDir = ''
    showCmd = win32con.SW_SHOWNORMAL
    #showCmd = win32con.SW_HIDE
    lpVerb = 'runas'  # causes UAC elevation prompt.

    # ShellExecute() doesn't seem to allow us to fetch the PID or handle
    # of the process, so we can't get anything useful from it. Therefore
    # the more complex ShellExecuteEx() must be used.

    # procHandle = win32api.ShellExecute(0, lpVerb, cmd, params, cmdDir, showCmd)

    procInfo = ShellExecuteEx(nShow=showCmd,
                              fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                              lpVerb=lpVerb,
                              lpFile=cmd,
                              lpParameters=params)

    if wait:
        procHandle = procInfo['hProcess']
        obj = win32event.WaitForSingleObject(procHandle, win32event.INFINITE)
        obj
        rc = win32process.GetExitCodeProcess(procHandle)
    else:
        rc = None

    return rc

if __name__ == '__main__':
    userIsAdmin = isUserAdmin()
    print('userIsAdmin = %d' % (userIsAdmin))
    if not userIsAdmin:
        runAsAdmin([sys.executable] + sys.argv, wait=True)
