# this script is used on windows to wrap shortcuts so that they are executed within an environment
#   It only sets the appropriate prefix PATH entries - it does not actually activate environments

from os
import sys
import subprocess
from os.path import join, pathsep

from menuinst.knownfolders import FOLDERID, get_folder_path, PathNotFoundException

# call as: python cwp.py PREFIX ARGs...

prefix = sys.argv[1]
args = sys.argv[2:]

new_paths = pathsep.join([prefix,
                         join(prefix, "Library", "mingw-w64", "bin"),
                         join(prefix, "Library", "usr", "bin"),
                         join(prefix, "Library", "bin"),
                         join(prefix, "Scripts")])

# Option 2 + 3 (in the try: block) requires a change to conda:
# https://github.com/conda/conda/pull/4406
# so option 3 is for older condas, but
# hardcoding is going to be faster.
# try:
#     from conda.cli.activate import get_activate_path
#     new_paths = get_activate_path(prefix, 'cmd.exe')
# except:
#     # Option 3 (I do not like hacking creationflags here)
#     CREATE_NO_WINDOW=0x08000000
#     new_paths = str(subprocess.check_output([join(prefix, "Scripts", "conda"), '..activate', 'cmd.exe', prefix],
#                                             creationflags=CREATE_NO_WINDOW))

env = os.environ.copy()
env['PATH'] = new_paths + pathsep + env['PATH']
env['CONDA_PREFIX'] = prefix

try:
    documents_folder = get_folder_path(FOLDERID.Documents)
except PathNotFoundException:
    documents_folder = get_folder_path(FOLDERID.PublicDocuments)
os.chdir(documents_folder)
subprocess.call(args, env=env)
