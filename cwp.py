import os
import sys
import subprocess
from os.path import join
import ctypes, ctypes.wintypes
import logging
CSIDL_PERSONAL=5
SHGFP_TYPE_CURRENT=0
CSIDL_COMMON_DOCUMENTS=46
CSIDL_COMMON_STARTMENU=22

# call as: python cwp.py PREFIX ARGs...

prefix = sys.argv[1]
args = sys.argv[2:]

env = os.environ.copy()
env['PATH'] = os.path.pathsep.join([
        prefix,
        join(prefix, "Scripts"),
        join(prefix, "Library", "bin"),
        env['PATH'],
])
buf=ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
if ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_PERSONAL, 0, SHGFP_TYPE_CURRENT, buf):
    ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_COMMON_DOCUMENTS, 0, SHGFP_TYPE_CURRENT, buf)
os.chdir(buf.value)
subprocess.call(args, env=env)
