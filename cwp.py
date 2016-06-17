# this script is used on windows to wrap shortcuts so that they are executed within an environment
#   It only sets the appropriate prefix PATH entries - it does not actually activate environments

import os
import sys
import subprocess
from os.path import join

# call as: python cwp.py PREFIX ARGs...

prefix = sys.argv[1]
cwd = sys.argv[2]
args = sys.argv[3:]

env = os.environ.copy()
env['PATH'] = os.path.pathsep.join([
        prefix,
        join(prefix, "Scripts"),
        join(prefix, "Library", "bin"),
        join(prefix, "Library", "usr", "bin"),
        join(prefix, "Library", "mingw-64", "bin"),
        env['PATH'],
])

subprocess.call(args, env=env, cwd=cwd)
