import os
import sys
import subprocess
from os.path import join

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
subprocess.call(args, env=env)
