/*
  IMPORTANT NOTE: IF THIS FILE IS CHANGED, WININST-6.EXE MUST BE RECOMPILED
  WITH THE MSVC6 WININST.DSW WORKSPACE FILE MANUALLY, AND WININST-7.1.EXE MUST
  BE RECOMPILED WITH THE MSVC 2003.NET WININST-7.1.VCPROJ FILE MANUALLY.

  IF CHANGES TO THIS FILE ARE CHECKED INTO PYTHON CVS, THE RECOMPILED BINARIES
  MUST BE CHECKED IN AS WELL!
*/

/*
 * Written by Thomas Heller, May 2000
 *
 * $Id: install.c 38415 2005-02-03 20:37:04Z theller $
 */

/*
 * Windows Installer program for distutils.
 *
 * (a kind of self-extracting zip-file)
 *
 * At runtime, the exefile has appended:
 * - compressed setup-data in ini-format, containing the following sections:
 *      [metadata]
 *      author=Greg Ward
 *      author_email=gward@python.net
 *      description=Python Distribution Utilities
 *      licence=Python
 *      name=Distutils
 *      url=http://www.python.org/sigs/distutils-sig/
 *      version=0.9pre
 *
 *      [Setup]
 *      info= text to be displayed in the edit-box
 *      title= to be displayed by this program
 *      target_version = if present, python version required
 *      pyc_compile = if 0, do not compile py to pyc
 *      pyo_compile = if 0, do not compile py to pyo
 *
 * - a struct meta_data_hdr, describing the above
 * - a zip-file, containing the modules to be installed.
 *   for the format see http://www.pkware.com/appnote.html
 *
 * What does this program do?
 * - the setup-data is uncompressed and written to a temporary file.
 * - setup-data is queried with GetPrivateProfile... calls
 * - [metadata] - info is displayed in the dialog box
 * - The registry is searched for installations of python
 * - The user can select the python version to use.
 * - The python-installation directory (sys.prefix) is displayed
 * - When the start-button is pressed, files from the zip-archive
 *   are extracted to the file system. All .py filenames are stored
 *   in a list.
 */
/*
 * Includes now an uninstaller.
 */

/*
 * To Do:
 *
 * display some explanation when no python version is found
 * instead showing the user an empty listbox to select something from.
 *
 * Finish the code so that we can use other python installations
 * additionaly to those found in the registry,
 * and then #define USE_OTHER_PYTHON_VERSIONS
 *
 *  - install a help-button, which will display something meaningful
 *    to the poor user.
 *    text to the user
 *  - should there be a possibility to display a README file
 *    before starting the installation (if one is present in the archive)
 *  - more comments about what the code does(?)
 *
 *  - evolve this into a full blown installer (???)
 *
 *  - include knownfolders.h when being built on Vista so that Vista-specific
 *  constants can be used (shlobj.h works on XP)
 */

#include <python.h>

#include <windows.h>
#include <commctrl.h>
#include <imagehlp.h>
#include <objbase.h>
#include <shlobj.h>
#include <objidl.h>
#include "resource.h"

#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <time.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <malloc.h>
#include <io.h>
#include <fcntl.h>

/* Only for debugging!
   static int dprintf(char *fmt, ...)
   {
   char Buffer[4096];
   va_list marker;
   int result;

   va_start(marker, fmt);
   result = wvsprintf(Buffer, fmt, marker);
   OutputDebugString(Buffer);
   return result;
   }
*/

/* codes for NOITIFYPROC */
#define DIR_CREATED 1
#define CAN_OVERWRITE 2
#define FILE_CREATED 3
#define ZLIB_ERROR 4
#define SYSTEM_ERROR 5
#define NUM_FILES 6
#define FILE_OVERWRITTEN 7


/* Bah: global variables */
FILE *logfile;

char modulename[MAX_PATH];

HWND hwndMain;
HWND hDialog;

char *ini_file;                 /* Full pathname of ini-file */
/* From ini-file */
char info[4096];                /* [Setup] info= */
char title[80];                 /* [Setup] title=, contains package name
                                   including version: "Distutils-1.0.1" */
char target_version[10];        /* [Setup] target_version=, required python
                                   version or empty string */
char build_info[80];            /* [Setup] build_info=, distutils version
                                   and build date */

char meta_name[80];             /* package name without version like
                                   'Distutils' */
char install_script[MAX_PATH];
char *pre_install_script; /* run before we install a single file */


int py_major, py_minor;         /* Python version selected for installation */

char *arc_data;                 /* memory mapped archive */
DWORD arc_size;                 /* number of bytes in archive */
int exe_size;                   /* number of bytes for exe-file portion */
char python_dir[MAX_PATH];
char pythondll[MAX_PATH];
BOOL pyc_compile, pyo_compile;
/* Either HKLM or HKCU, depending on where Python itself is registered, and
   the permissions of the current user. */
HKEY hkey_root = (HKEY)-1;

BOOL success;                   /* Installation successfull? */
char *failure_reason = NULL;

HANDLE hBitmap;
char *bitmap_bytes;


#define WM_NUMFILES WM_USER+1
/* wParam: 0, lParam: total number of files */
#define WM_NEXTFILE WM_USER+2
/* wParam: number of this file */
/* lParam: points to pathname */

static BOOL notify(int code, char *fmt, ...);

static struct tagFile {
        char *path;
        struct tagFile *next;
} *file_list = NULL;


static void add_to_filelist(char *path)
{
        struct tagFile *p;
        p = (struct tagFile *)malloc(sizeof(struct tagFile));
        p->path = strdup(path);
        p->next = file_list;
        file_list = p;
}


#define DEF_CSIDL(name) { name, #name }

struct {
        int nFolder;
        char *name;
} csidl_names[] = {
        /* Startup menu for all users.
           NT only */
        DEF_CSIDL(CSIDL_COMMON_STARTMENU),
        /* Startup menu. */
        DEF_CSIDL(CSIDL_STARTMENU),

/*    DEF_CSIDL(CSIDL_COMMON_APPDATA), */
/*    DEF_CSIDL(CSIDL_LOCAL_APPDATA), */
        /* Repository for application-specific data.
           Needs Internet Explorer 4.0 */
        DEF_CSIDL(CSIDL_APPDATA),

        /* The desktop for all users.
           NT only */
        DEF_CSIDL(CSIDL_COMMON_DESKTOPDIRECTORY),
        /* The desktop. */
        DEF_CSIDL(CSIDL_DESKTOPDIRECTORY),

        /* Startup folder for all users.
           NT only */
        DEF_CSIDL(CSIDL_COMMON_STARTUP),
        /* Startup folder. */
        DEF_CSIDL(CSIDL_STARTUP),

        /* Programs item in the start menu for all users.
           NT only */
        DEF_CSIDL(CSIDL_COMMON_PROGRAMS),
        /* Program item in the user's start menu. */
        DEF_CSIDL(CSIDL_PROGRAMS),

/*    DEF_CSIDL(CSIDL_PROGRAM_FILES_COMMON), */
/*    DEF_CSIDL(CSIDL_PROGRAM_FILES), */

        /* Virtual folder containing fonts. */
        DEF_CSIDL(CSIDL_FONTS),
};

#define DIM(a) (sizeof(a) / sizeof((a)[0]))

static PyObject *FileCreated(PyObject *self, PyObject *args)
{
        char *path;
        if (!PyArg_ParseTuple(args, "s", &path))
                return NULL;
        notify(FILE_CREATED, path);
        return Py_BuildValue("");
}

static PyObject *DirectoryCreated(PyObject *self, PyObject *args)
{
        char *path;
        if (!PyArg_ParseTuple(args, "s", &path))
                return NULL;
        notify(DIR_CREATED, path);
        return Py_BuildValue("");
}

static PyObject *GetSpecialFolderPath(PyObject *self, PyObject *args)
{
        char *name;
        char lpszPath[MAX_PATH];
        int i;
        static HRESULT (WINAPI *My_SHGetSpecialFolderPath)(HWND hwnd,
                                                           LPTSTR lpszPath,
                                                           int nFolder,
                                                           BOOL fCreate);

        if (!My_SHGetSpecialFolderPath) {
                HINSTANCE hLib = LoadLibrary("shell32.dll");
                if (!hLib) {
                        PyErr_Format(PyExc_OSError,
                                       "function not available");
                        return NULL;
                }
                My_SHGetSpecialFolderPath = (BOOL (WINAPI *)(HWND, LPTSTR,
                                                             int, BOOL))
                        GetProcAddress(hLib,
                                       "SHGetSpecialFolderPathA");
        }

        if (!PyArg_ParseTuple(args, "s", &name))
                return NULL;

        if (!My_SHGetSpecialFolderPath) {
                PyErr_Format(PyExc_OSError, "function not available");
                return NULL;
        }

        for (i = 0; i < DIM(csidl_names); ++i) {
                if (0 == strcmpi(csidl_names[i].name, name)) {
                        int nFolder;
                        nFolder = csidl_names[i].nFolder;
                        if (My_SHGetSpecialFolderPath(NULL, lpszPath,
                                                      nFolder, 0))
                                return Py_BuildValue("s", lpszPath);
                        else {
                                PyErr_Format(PyExc_OSError,
                                               "no such folder (%s)", name);
                                return NULL;
                        }

                }
        };
        PyErr_Format(PyExc_ValueError, "unknown CSIDL (%s)", name);
        return NULL;
}

static PyObject *CreateShortcut(PyObject *self, PyObject *args)
{
        char *path; /* path and filename */
        char *description;
        char *filename;

        char *arguments = NULL;
        char *iconpath = NULL;
        int iconindex = 0;
        char *workdir = NULL;

        WCHAR wszFilename[MAX_PATH];

        IShellLink *ps1 = NULL;
        IPersistFile *pPf = NULL;

        HRESULT hr;

        hr = CoInitialize(NULL);
        if (FAILED(hr)) {
                PyErr_Format(PyExc_OSError,
                               "CoInitialize failed, error 0x%x", hr);
                goto error;
        }

        if (!PyArg_ParseTuple(args, "sss|sssi",
                                &path, &description, &filename,
                                &arguments, &workdir, &iconpath, &iconindex))
                return NULL;

        hr = CoCreateInstance(&CLSID_ShellLink,
                              NULL,
                              CLSCTX_INPROC_SERVER,
                              &IID_IShellLink,
                              &ps1);
        if (FAILED(hr)) {
                PyErr_Format(PyExc_OSError,
                               "CoCreateInstance failed, error 0x%x", hr);
                goto error;
        }

        hr = ps1->lpVtbl->QueryInterface(ps1, &IID_IPersistFile,
                                         (void **)&pPf);
        if (FAILED(hr)) {
                PyErr_Format(PyExc_OSError,
                               "QueryInterface(IPersistFile) error 0x%x", hr);
                goto error;
        }


        hr = ps1->lpVtbl->SetPath(ps1, path);
        if (FAILED(hr)) {
                PyErr_Format(PyExc_OSError,
                               "SetPath() failed, error 0x%x", hr);
                goto error;
        }

        hr = ps1->lpVtbl->SetDescription(ps1, description);
        if (FAILED(hr)) {
                PyErr_Format(PyExc_OSError,
                               "SetDescription() failed, error 0x%x", hr);
                goto error;
        }

        if (arguments) {
                hr = ps1->lpVtbl->SetArguments(ps1, arguments);
                if (FAILED(hr)) {
                        PyErr_Format(PyExc_OSError,
                                       "SetArguments() error 0x%x", hr);
                        goto error;
                }
        }

        if (iconpath) {
                hr = ps1->lpVtbl->SetIconLocation(ps1, iconpath, iconindex);
                if (FAILED(hr)) {
                        PyErr_Format(PyExc_OSError,
                                       "SetIconLocation() error 0x%x", hr);
                        goto error;
                }
        }

        if (workdir) {
                hr = ps1->lpVtbl->SetWorkingDirectory(ps1, workdir);
                if (FAILED(hr)) {
                        PyErr_Format(PyExc_OSError,
                                       "SetWorkingDirectory() error 0x%x", hr);
                        goto error;
                }
        }

        MultiByteToWideChar(CP_ACP, 0,
                            filename, -1,
                            wszFilename, MAX_PATH);

        hr = pPf->lpVtbl->Save(pPf, wszFilename, TRUE);
        if (FAILED(hr)) {
                PyErr_Format(PyExc_OSError,
                               "Failed to create shortcut '%s' - error 0x%x", filename, hr);
                goto error;
        }

        pPf->lpVtbl->Release(pPf);
        ps1->lpVtbl->Release(ps1);
        CoUninitialize();
        return Py_BuildValue("");

  error:
        if (pPf)
                pPf->lpVtbl->Release(pPf);

        if (ps1)
                ps1->lpVtbl->Release(ps1);

        CoUninitialize();

        return NULL;
}

static PyObject *PyMessageBox(PyObject *self, PyObject *args)
{
        int rc;
        char *text, *caption;
        int flags;
        if (!PyArg_ParseTuple(args, "ssi", &text, &caption, &flags))
                return NULL;
        rc = MessageBox(GetFocus(), text, caption, flags);
        return Py_BuildValue("i", rc);
}

static PyObject *GetRootHKey(PyObject *self)
{
        return Py_BuildValue("l", hkey_root);
}

#define METH_VARARGS 0x0001
#define METH_NOARGS   0x0004
/*
   This is already defined in include/methodobject.h (line 18), and there
   is no reason to redefine it here.  In fact redefining it causes an error.

   typedef PyObject *(*PyCFunction)(PyObject *, PyObject *);
*/

PyMethodDef meth[] = {
        {"create_shortcut", CreateShortcut, METH_VARARGS, NULL},
        {"get_special_folder_path", GetSpecialFolderPath, METH_VARARGS, NULL},
        {"get_root_hkey", (PyCFunction)GetRootHKey, METH_NOARGS, NULL},
        {"file_created", FileCreated, METH_VARARGS, NULL},
        {"directory_created", DirectoryCreated, METH_VARARGS, NULL},
        {"message_box", PyMessageBox, METH_VARARGS, NULL},
    {NULL, NULL}
};

static int prepare_script_environment(HINSTANCE hPython)
{
        PyObject *mod;
        mod = PyImport_ImportModule("__builtin__");
        if (mod) {
                int i;
                PyExc_ValueError = PyObject_GetAttrString(mod, "ValueError");
                PyExc_OSError = PyObject_GetAttrString(mod, "OSError");
                for (i = 0; i < DIM(meth); ++i) {
                        PyObject_SetAttrString(mod, meth[i].ml_name,
                                               PyCFunction_New(&meth[i], NULL));
                }
        }

        return 0;
}

static BOOL SystemError(int error, char *msg)
{
        char Buffer[1024];
        int n;

        if (error) {
                LPVOID lpMsgBuf;
                FormatMessage(
                        FORMAT_MESSAGE_ALLOCATE_BUFFER |
                        FORMAT_MESSAGE_FROM_SYSTEM,
                        NULL,
                        error,
                        MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
                        (LPSTR)&lpMsgBuf,
                        0,
                        NULL
                        );
                strncpy(Buffer, lpMsgBuf, sizeof(Buffer));
                LocalFree(lpMsgBuf);
        } else
                Buffer[0] = '\0';
        n = lstrlen(Buffer);
        _snprintf(Buffer+n, sizeof(Buffer)-n, msg);
        MessageBox(hwndMain, Buffer, "Runtime Error", MB_OK | MB_ICONSTOP);
        return FALSE;
}

static BOOL notify (int code, char *fmt, ...)
{
        char Buffer[1024];
        va_list marker;
        BOOL result = TRUE;
        int a, b;
        char *cp;

        va_start(marker, fmt);
        _vsnprintf(Buffer, sizeof(Buffer), fmt, marker);

        switch (code) {
/* Questions */
        case CAN_OVERWRITE:
                break;

/* Information notification */
        case DIR_CREATED:
                if (logfile)
                        fprintf(logfile, "100 Made Dir: %s\n", fmt);
                break;

        case FILE_CREATED:
                if (logfile)
                        fprintf(logfile, "200 File Copy: %s\n", fmt);
                goto add_to_filelist_label;
                break;

        case FILE_OVERWRITTEN:
                if (logfile)
                        fprintf(logfile, "200 File Overwrite: %s\n", fmt);
          add_to_filelist_label:
                if ((cp = strrchr(fmt, '.')) && (0 == strcmp (cp, ".py")))
                        add_to_filelist(fmt);
                break;

/* Error Messages */
        case ZLIB_ERROR:
                MessageBox(GetFocus(), Buffer, "Error",
                            MB_OK | MB_ICONWARNING);
                break;

        case SYSTEM_ERROR:
                SystemError(GetLastError(), Buffer);
                break;

        case NUM_FILES:
                a = va_arg(marker, int);
                b = va_arg(marker, int);
                SendMessage(hDialog, WM_NUMFILES, 0, MAKELPARAM(0, a));
                SendMessage(hDialog, WM_NEXTFILE, b,(LPARAM)fmt);
        }
        va_end(marker);

        return result;
}

static char *MapExistingFile(char *pathname, DWORD *psize)
{
        HANDLE hFile, hFileMapping;
        DWORD nSizeLow, nSizeHigh;
        char *data;

        hFile = CreateFile(pathname,
                            GENERIC_READ, FILE_SHARE_READ, NULL,
                            OPEN_EXISTING,
                            FILE_ATTRIBUTE_NORMAL, NULL);
        if (hFile == INVALID_HANDLE_VALUE)
                return NULL;
        nSizeLow = GetFileSize(hFile, &nSizeHigh);
        hFileMapping = CreateFileMapping(hFile,
                                          NULL, PAGE_READONLY, 0, 0, NULL);
        CloseHandle(hFile);

        if (hFileMapping == INVALID_HANDLE_VALUE)
                return NULL;

        data = MapViewOfFile(hFileMapping,
                              FILE_MAP_READ, 0, 0, 0);

        CloseHandle(hFileMapping);
        *psize = nSizeLow;
        return data;
}


static void create_bitmap(HWND hwnd)
{
        BITMAPFILEHEADER *bfh;
        BITMAPINFO *bi;
        HDC hdc;

        if (!bitmap_bytes)
                return;

        if (hBitmap)
                return;

        hdc = GetDC(hwnd);

        bfh = (BITMAPFILEHEADER *)bitmap_bytes;
        bi = (BITMAPINFO *)(bitmap_bytes + sizeof(BITMAPFILEHEADER));

        hBitmap = CreateDIBitmap(hdc,
                                 &bi->bmiHeader,
                                 CBM_INIT,
                                 bitmap_bytes + bfh->bfOffBits,
                                 bi,
                                 DIB_RGB_COLORS);
        ReleaseDC(hwnd, hdc);
}



#ifdef USE_OTHER_PYTHON_VERSIONS
/* These are really private variables used to communicate
 * between StatusRoutine and CheckPythonExe
 */
char bound_image_dll[_MAX_PATH];
int bound_image_major;
int bound_image_minor;

static BOOL __stdcall StatusRoutine(IMAGEHLP_STATUS_REASON reason,
                                    PSTR ImageName,
                                    PSTR DllName,
                                    ULONG Va,
                                    ULONG Parameter)
{
        char fname[_MAX_PATH];
        int int_version;

        switch(reason) {
        case BindOutOfMemory:
        case BindRvaToVaFailed:
        case BindNoRoomInImage:
        case BindImportProcedureFailed:
                break;

        case BindImportProcedure:
        case BindForwarder:
        case BindForwarderNOT:
        case BindImageModified:
        case BindExpandFileHeaders:
        case BindImageComplete:
        case BindSymbolsNotUpdated:
        case BindMismatchedSymbols:
        case BindImportModuleFailed:
                break;

        case BindImportModule:
                if (1 == sscanf(DllName, "python%d", &int_version)) {
                        SearchPath(NULL, DllName, NULL, sizeof(fname),
                                   fname, NULL);
                        strcpy(bound_image_dll, fname);
                        bound_image_major = int_version / 10;
                        bound_image_minor = int_version % 10;
                        OutputDebugString("BOUND ");
                        OutputDebugString(fname);
                        OutputDebugString("\n");
                }
                break;
        }
        return TRUE;
}

/*
 */
static LPSTR get_sys_prefix(LPSTR exe, LPSTR dll)
{
        void (__cdecl * Py_Initialize)(void);
        void (__cdecl * Py_SetProgramName)(char *);
        void (__cdecl * Py_Finalize)(void);
        void* (__cdecl * PySys_GetObject)(char *);
        void (__cdecl * PySys_SetArgv)(int, char **);
        char* (__cdecl * Py_GetPrefix)(void);
        char* (__cdecl * Py_GetPath)(void);
        LPSTR prefix = NULL;
        int (__cdecl * PyRun_SimpleString)(char *);

        {
                char Buffer[256];
                wsprintf(Buffer, "PYTHONHOME=%s", exe);
                *strrchr(Buffer, '\\') = '\0';
//      MessageBox(GetFocus(), Buffer, "PYTHONHOME", MB_OK);
                _putenv(Buffer);
                _putenv("PYTHONPATH=");
        }

        MessageBox(GetFocus(), Py_GetPrefix(), "PREFIX", MB_OK);
        MessageBox(GetFocus(), Py_GetPath(), "PATH", MB_OK);

        return prefix;
}

static BOOL
CheckPythonExe(LPSTR pathname, LPSTR version, int *pmajor, int *pminor)
{
        bound_image_dll[0] = '\0';
        if (!BindImageEx(BIND_NO_BOUND_IMPORTS | BIND_NO_UPDATE | BIND_ALL_IMAGES,
                         pathname,
                         NULL,
                         NULL,
                         StatusRoutine))
                return SystemError(0, "Could not bind image");
        if (bound_image_dll[0] == '\0')
                return SystemError(0, "Does not seem to be a python executable");
        *pmajor = bound_image_major;
        *pminor = bound_image_minor;
        if (version && *version) {
                char core_version[12];
                wsprintf(core_version, "%d.%d", bound_image_major, bound_image_minor);
                if (strcmp(version, core_version))
                        return SystemError(0, "Wrong Python version");
        }
        get_sys_prefix(pathname, bound_image_dll);
        return TRUE;
}

/*
 * Browse for other python versions. Insert it into the listbox specified
 * by hwnd. version, if not NULL or empty, is the version required.
 */
static BOOL GetOtherPythonVersion(HWND hwnd, LPSTR version)
{
        char vers_name[_MAX_PATH + 80];
        DWORD itemindex;
        OPENFILENAME of;
        char pathname[_MAX_PATH];
        DWORD result;

        strcpy(pathname, "python.exe");

        memset(&of, 0, sizeof(of));
        of.lStructSize = sizeof(OPENFILENAME);
        of.hwndOwner = GetParent(hwnd);
        of.hInstance = NULL;
        of.lpstrFilter = "python.exe\0python.exe\0";
        of.lpstrCustomFilter = NULL;
        of.nMaxCustFilter = 0;
        of.nFilterIndex = 1;
        of.lpstrFile = pathname;
        of.nMaxFile = sizeof(pathname);
        of.lpstrFileTitle = NULL;
        of.nMaxFileTitle = 0;
        of.lpstrInitialDir = NULL;
        of.lpstrTitle = "Python executable";
        of.Flags = OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST;
        of.lpstrDefExt = "exe";

        result = GetOpenFileName(&of);
        if (result) {
                int major, minor;
                if (!CheckPythonExe(pathname, version, &major, &minor)) {
                        return FALSE;
                }
                *strrchr(pathname, '\\') = '\0';
                wsprintf(vers_name, "Python Version %d.%d in %s",
                          major, minor, pathname);
                itemindex = SendMessage(hwnd, LB_INSERTSTRING, -1,
                                        (LPARAM)(LPSTR)vers_name);
                SendMessage(hwnd, LB_SETCURSEL, itemindex, 0);
                SendMessage(hwnd, LB_SETITEMDATA, itemindex,
                            (LPARAM)(LPSTR)strdup(pathname));
                return TRUE;
        }
        return FALSE;
}
#endif /* USE_OTHER_PYTHON_VERSIONS */

typedef struct _InstalledVersionInfo {
    char prefix[MAX_PATH+1]; // sys.prefix directory.
    HKEY hkey; // Is this Python in HKCU or HKLM?
} InstalledVersionInfo;


/*
 * Fill the listbox specified by hwnd with all python versions found
 * in the registry. version, if not NULL or empty, is the version
 * required.
 */
static BOOL GetPythonVersions(HWND hwnd, HKEY hkRoot, LPSTR version)
{
        DWORD index = 0;
        char core_version[80];
        HKEY hKey;
        BOOL result = TRUE;
        DWORD bufsize;

        if (ERROR_SUCCESS != RegOpenKeyEx(hkRoot,
                                           "Software\\Python\\PythonCore",
                                           0,   KEY_READ, &hKey))
                return FALSE;
        bufsize = sizeof(core_version);
        while (ERROR_SUCCESS == RegEnumKeyEx(hKey, index,
                                              core_version, &bufsize, NULL,
                                              NULL, NULL, NULL)) {
                char subkey_name[80], vers_name[80];
                int itemindex;
                DWORD value_size;
                HKEY hk;

                bufsize = sizeof(core_version);
                ++index;
                if (version && *version && strcmp(version, core_version))
                        continue;

                wsprintf(vers_name, "Python Version %s (found in registry)",
                          core_version);
                wsprintf(subkey_name,
                          "Software\\Python\\PythonCore\\%s\\InstallPath",
                          core_version);
                if (ERROR_SUCCESS == RegOpenKeyEx(hkRoot, subkey_name, 0, KEY_READ, &hk)) {
                        InstalledVersionInfo *ivi =
                              (InstalledVersionInfo *)malloc(sizeof(InstalledVersionInfo));
                        value_size = sizeof(ivi->prefix);
                        if (ivi &&
                            ERROR_SUCCESS == RegQueryValueEx(hk, NULL, NULL, NULL,
                                                             ivi->prefix, &value_size)) {
                                itemindex = SendMessage(hwnd, LB_ADDSTRING, 0,
                                                        (LPARAM)(LPSTR)vers_name);
                                ivi->hkey = hkRoot;
                                SendMessage(hwnd, LB_SETITEMDATA, itemindex,
                                            (LPARAM)(LPSTR)ivi);
                        }
                        RegCloseKey(hk);
                }
        }
        RegCloseKey(hKey);
        return result;
}

/* Determine if the current user can write to HKEY_LOCAL_MACHINE */
BOOL HasLocalMachinePrivs()
{
                HKEY hKey;
                DWORD result;
                static char KeyName[] =
                        "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall";

                result = RegOpenKeyEx(HKEY_LOCAL_MACHINE,
                                          KeyName,
                                          0,
                                          KEY_CREATE_SUB_KEY,
                                          &hKey);
                if (result==0)
                        RegCloseKey(hKey);
                return result==0;
}

// Check the root registry key to use - either HKLM or HKCU.
// If Python is installed in HKCU, then our extension also must be installed
// in HKCU - as Python won't be available for other users, we shouldn't either
// (and will fail if we are!)
// If Python is installed in HKLM, then we will also prefer to use HKLM, but
// this may not be possible - so we silently fall back to HKCU.
//
// We assume hkey_root is already set to where Python itself is installed.
void CheckRootKey(HWND hwnd)
{
        if (hkey_root==HKEY_CURRENT_USER) {
                ; // as above, always install ourself in HKCU too.
        } else if (hkey_root==HKEY_LOCAL_MACHINE) {
                // Python in HKLM, but we may or may not have permissions there.
                // Open the uninstall key with 'create' permissions - if this fails,
                // we don't have permission.
                if (!HasLocalMachinePrivs())
                        hkey_root = HKEY_CURRENT_USER;
        } else {
                MessageBox(hwnd, "Don't know Python's installation type",
                                   "Strange", MB_OK | MB_ICONSTOP);
                /* Default to wherever they can, but preferring HKLM */
                hkey_root = HasLocalMachinePrivs() ? HKEY_LOCAL_MACHINE : HKEY_CURRENT_USER;
        }
}

static BOOL OpenLogfile(char *dir)
{
        char buffer[_MAX_PATH+1];
        time_t ltime;
        struct tm *now;
        long result;
        HKEY hKey, hSubkey;
        char subkey_name[256];
        static char KeyName[] =
                "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall";
        const char *root_name = (hkey_root==HKEY_LOCAL_MACHINE ?
                                "HKEY_LOCAL_MACHINE" : "HKEY_CURRENT_USER");
        DWORD disposition;

        /* Use Create, as the Uninstall subkey may not exist under HKCU.
           Use CreateKeyEx, so we can specify a SAM specifying write access
        */
                result = RegCreateKeyEx(hkey_root,
                              KeyName,
                              0, /* reserved */
                              NULL, /* class */
                              0, /* options */
                              KEY_CREATE_SUB_KEY, /* sam */
                              NULL, /* security */
                              &hKey, /* result key */
                              NULL); /* disposition */
        if (result != ERROR_SUCCESS) {
                if (result == ERROR_ACCESS_DENIED) {
                        /* This should no longer be able to happen - we have already
                           checked if they have permissions in HKLM, and all users
                           should have write access to HKCU.
                        */
                        MessageBox(GetFocus(),
                                   "You do not seem to have sufficient access rights\n"
                                   "on this machine to install this software",
                                   NULL,
                                   MB_OK | MB_ICONSTOP);
                        return FALSE;
                } else {
                        MessageBox(GetFocus(), KeyName, "Could not open key", MB_OK);
                }
        }

        sprintf(buffer, "%s\\%s-appinst.log", dir, meta_name);
        logfile = fopen(buffer, "a");
        time(&ltime);
        now = localtime(&ltime);
        strftime(buffer, sizeof(buffer),
                 "*** Installation started %Y/%m/%d %H:%M ***\n",
                 localtime(&ltime));
        fprintf(logfile, buffer);
        fprintf(logfile, "Source: %s\n", modulename);

        /* Root key must be first entry processed by uninstaller. */
        fprintf(logfile, "999 Root Key: %s\n", root_name);

        sprintf(subkey_name, "%s-py%d.%d", meta_name, py_major, py_minor);

        result = RegCreateKeyEx(hKey, subkey_name,
                                0, NULL, 0,
                                KEY_WRITE,
                                NULL,
                                &hSubkey,
                                &disposition);

        if (result != ERROR_SUCCESS)
                MessageBox(GetFocus(), subkey_name, "Could not create key", MB_OK);

        RegCloseKey(hKey);

        if (disposition == REG_CREATED_NEW_KEY)
                fprintf(logfile, "020 Reg DB Key: [%s]%s\n", KeyName, subkey_name);

        sprintf(buffer, "Python %d.%d %s", py_major, py_minor, title);

        result = RegSetValueEx(hSubkey, "DisplayName",
                               0,
                               REG_SZ,
                               buffer,
                               strlen(buffer)+1);

        if (result != ERROR_SUCCESS)
                MessageBox(GetFocus(), buffer, "Could not set key value", MB_OK);

        fprintf(logfile, "040 Reg DB Value: [%s\\%s]%s=%s\n",
                KeyName, subkey_name, "DisplayName", buffer);

        {
                FILE *fp;
                sprintf(buffer, "%s\\Remove%s.exe", dir, meta_name);
                fp = fopen(buffer, "wb");
                fwrite(arc_data, exe_size, 1, fp);
                fclose(fp);

                sprintf(buffer, "\"%s\\Remove%s.exe\" -u \"%s\\%s-appinst.log\"",
                        dir, meta_name, dir, meta_name);

                result = RegSetValueEx(hSubkey, "UninstallString",
                                       0,
                                       REG_SZ,
                                       buffer,
                                       strlen(buffer)+1);

                if (result != ERROR_SUCCESS)
                        MessageBox(GetFocus(), buffer, "Could not set key value", MB_OK);

                fprintf(logfile, "040 Reg DB Value: [%s\\%s]%s=%s\n",
                        KeyName, subkey_name, "UninstallString", buffer);
        }
        return TRUE;
}

static void CloseLogfile(void)
{
        char buffer[_MAX_PATH+1];
        time_t ltime;
        struct tm *now;

        time(&ltime);
        now = localtime(&ltime);
        strftime(buffer, sizeof(buffer),
                 "*** Installation finished %Y/%m/%d %H:%M ***\n",
                 localtime(&ltime));
        fprintf(logfile, buffer);
        if (logfile)
                fclose(logfile);
}

/*********************** uninstall section ******************************/

static int compare(const void *p1, const void *p2)
{
        return strcmp(*(char **)p2, *(char **)p1);
}

/*
 * Commit suicide (remove the uninstaller itself).
 *
 * Create a batch file to first remove the uninstaller
 * (will succeed after it has finished), then the batch file itself.
 *
 * This technique has been demonstrated by Jeff Richter,
 * MSJ 1/1996
 */
void remove_exe(void)
{
        char exename[_MAX_PATH];
        char batname[_MAX_PATH];
        FILE *fp;
        STARTUPINFO si;
        PROCESS_INFORMATION pi;

        GetModuleFileName(NULL, exename, sizeof(exename));
        sprintf(batname, "%s.bat", exename);
        fp = fopen(batname, "w");
        fprintf(fp, ":Repeat\n");
        fprintf(fp, "del \"%s\"\n", exename);
        fprintf(fp, "if exist \"%s\" goto Repeat\n", exename);
        fprintf(fp, "del \"%s\"\n", batname);
        fclose(fp);

        ZeroMemory(&si, sizeof(si));
        si.cb = sizeof(si);
        si.dwFlags = STARTF_USESHOWWINDOW;
        si.wShowWindow = SW_HIDE;
        if (CreateProcess(NULL,
                          batname,
                          NULL,
                          NULL,
                          FALSE,
                          CREATE_SUSPENDED | IDLE_PRIORITY_CLASS,
                          NULL,
                          "\\",
                          &si,
                          &pi)) {
                SetThreadPriority(pi.hThread, THREAD_PRIORITY_IDLE);
                SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_TIME_CRITICAL);
                SetPriorityClass(GetCurrentProcess(), HIGH_PRIORITY_CLASS);
                CloseHandle(pi.hProcess);
                ResumeThread(pi.hThread);
                CloseHandle(pi.hThread);
        }
}

void DeleteRegistryKey(char *string)
{
        char *keyname;
        char *subkeyname;
        char *delim;
        HKEY hKey;
        long result;
        char *line;

        line = strdup(string); /* so we can change it */

        keyname = strchr(line, '[');
        if (!keyname)
                return;
        ++keyname;

        subkeyname = strchr(keyname, ']');
        if (!subkeyname)
                return;
        *subkeyname++='\0';
        delim = strchr(subkeyname, '\n');
        if (delim)
                *delim = '\0';

        result = RegOpenKeyEx(hkey_root,
                              keyname,
                              0,
                              KEY_WRITE,
                              &hKey);

        if (result != ERROR_SUCCESS)
                MessageBox(GetFocus(), string, "Could not open key", MB_OK);
        else {
                result = RegDeleteKey(hKey, subkeyname);
                if (result != ERROR_SUCCESS && result != ERROR_FILE_NOT_FOUND)
                        MessageBox(GetFocus(), string, "Could not delete key", MB_OK);
                RegCloseKey(hKey);
        }
        free(line);
}

void DeleteRegistryValue(char *string)
{
        char *keyname;
        char *valuename;
        char *value;
        HKEY hKey;
        long result;
        char *line;

        line = strdup(string); /* so we can change it */

/* Format is 'Reg DB Value: [key]name=value' */
        keyname = strchr(line, '[');
        if (!keyname)
                return;
        ++keyname;
        valuename = strchr(keyname, ']');
        if (!valuename)
                return;
        *valuename++ = '\0';
        value = strchr(valuename, '=');
        if (!value)
                return;

        *value++ = '\0';

        result = RegOpenKeyEx(hkey_root,
                              keyname,
                              0,
                              KEY_WRITE,
                              &hKey);
        if (result != ERROR_SUCCESS)
                MessageBox(GetFocus(), string, "Could not open key", MB_OK);
        else {
                result = RegDeleteValue(hKey, valuename);
                if (result != ERROR_SUCCESS && result != ERROR_FILE_NOT_FOUND)
                        MessageBox(GetFocus(), string, "Could not delete value", MB_OK);
                RegCloseKey(hKey);
        }
        free(line);
}

BOOL MyDeleteFile(char *line)
{
        char *pathname = strchr(line, ':');
        if (!pathname)
                return FALSE;
        ++pathname;
        while (isspace(*pathname))
                ++pathname;
        return DeleteFile(pathname);
}

BOOL MyRemoveDirectory(char *line)
{
        char *pathname = strchr(line, ':');
        if (!pathname)
                return FALSE;
        ++pathname;
        while (isspace(*pathname))
                ++pathname;
        return RemoveDirectory(pathname);
}

void initwininst(void)
{
        Py_InitModule("wininst", meth);
}
