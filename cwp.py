# this script is used on windows to wrap shortcuts so that they are executed within an environment
#   It only sets the appropriate prefix PATH entries - it does not actually activate environments

import os
import sys
import subprocess
from os.path import join

from menuinst.knownfolders import FOLDERID, get_folder_path, PathNotFoundException

# call as: python cwp.py PREFIX ARGs...

prefix = sys.argv[1]
args = sys.argv[2:]

env = os.environ.copy()
env['PATH'] = os.path.pathsep.join([
        prefix,
        join(prefix, "Library", "mingw-w64", "bin"),
        join(prefix, "Scripts"),
        join(prefix, "Library", "bin"),
        env['PATH'],
])

try:
    documents_folder = get_folder_path(FOLDERID.Documents)
except PathNotFoundException:
    documents_folder = get_folder_path(FOLDERID.PublicDocuments)
os.chdir(documents_folder)
subprocess.call(args, env=env)
