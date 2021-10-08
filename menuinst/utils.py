import os
import sys
import shutil
from os.path import  isdir, isfile, islink, join

non_url_safe = ('"', '#', '$', '%', '&', '+',
                ',', '/', ':', ';', '=', '?',
                '@', '[', '\\', ']', '^', '`',
                '{', '|', '}', '~', "'")
translate_table = {ord(char): u'' for char in non_url_safe}
on_win = sys.platform == 'win32'

if on_win:
    bin_dir_name = 'Scripts'
    rel_site_packages = r'Lib\site-packages'
else:
    bin_dir_name = 'bin'
    rel_site_packages = 'lib/python%i.%i/site-packages' % sys.version_info[:2]


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


def get_executable(prefix):
    if on_win:
        paths = [prefix, join(prefix, bin_dir_name)]
        for path in paths:
            executable = join(path, 'python.exe')
            if isfile(executable):
                return executable
    else:
        path = join(prefix, bin_dir_name, 'python')
        if isfile(path):
            from subprocess import Popen, PIPE
            cmd = [path, '-c', 'import sys;print sys.executable']
            p = Popen(cmd, stdout=PIPE)
            return p.communicate()[0].strip()
    return sys.executable


def slugify(text):
    text = text.translate(translate_table)
    text = u'_'.join(text.split())
    return text
