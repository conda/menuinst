import ctypes
from ctypes import wintypes

__all__ = ['get_folder_path']

csidl_consts = {
    'CSIDL_COMMON_STARTMENU': 0x0016,
    'CSIDL_STARTMENU': 0x000b,
    'CSIDL_COMMON_APPDATA': 0x0023,
    'CSIDL_LOCAL_APPDATA': 0x001c,
    'CSIDL_APPDATA': 0x001a,
    'CSIDL_COMMON_DESKTOPDIRECTORY': 0x0019,
    'CSIDL_DESKTOPDIRECTORY': 0x0010,
    'CSIDL_COMMON_STARTUP': 0x0018,
    'CSIDL_STARTUP': 0x0007,
    'CSIDL_COMMON_PROGRAMS': 0x0017,
    'CSIDL_PROGRAMS': 0x0002,
    'CSIDL_PROGRAM_FILES_COMMON': 0x002b,
    'CSIDL_PROGRAM_FILES': 0x0026,
    'CSIDL_FONTS': 0x0014,
    'CSIDL_PROFILE': 0x0028,
    'CSIDL_PERSONAL': 0x0005,
}

SHGetFolderPath = ctypes.windll.shell32.SHGetFolderPathW
SHGetFolderPath.restype = wintypes.HANDLE
SHGetFolderPath.argtypes = [wintypes.HWND, ctypes.c_int,
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR]
SHGFP_TYPE_CURRENT = 0
SHGFP_TYPE_DEFAULT = 1
MAX_PATH = 260

def get_folder_path(path_name):
    csidl = csidl_consts.get(path_name, None)
    if csidl:
        out_str = ctypes.create_unicode_buffer(MAX_PATH)
        if SHGetFolderPath(None, csidl, None, SHGFP_TYPE_CURRENT, out_str):
            raise ctypes.WinError()
        return out_str.value
    else:
        raise ValueError("%s is an unknown CSIDL path ID" % (path_name))
