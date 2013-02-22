import os
import sys
import shutil
from os.path import isdir, isfile, islink


if sys.platform == 'win32':
    bin_dir_name = 'Scripts'
else:
    bin_dir_name = 'bin'


def rm_empty_dir(path):
    try:
        os.rmdir(path)
    except OSError: # directory might not exist or not be empty
        pass


def rm_rf(path):
    if islink(path) or isfile(path):
        # Note that we have to check if the destination is a link because
        # exists('/path/to/dead-link') will return False, although
        # islink('/path/to/dead-link') is True.
        os.unlink(path)

    elif isdir(path):
        shutil.rmtree(path)
