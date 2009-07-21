import sys
from os.path import isfile, join



def load_system_module(mod):
    """
    Loads the given module from the given directory, inserting the major and
    minor python version numbers in the module name.
    """
    import imp

    fn = "%s%d%d.dll" % (mod, sys.version_info[0], sys.version_info[1])
    path = join(sys.prefix, 'Scripts', fn)
    if isfile(path):
        imp.load_module(mod, None, path, ('.dll', 'rb', imp.C_EXTENSION))
    else:
        print "Warning: %r does not exist" % path


if sys.platform == 'win32':
    load_system_module("pywintypes")
    load_system_module("pythoncom")
