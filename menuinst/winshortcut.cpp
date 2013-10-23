
/*
 * Written by Thomas Heller, May 2000
 *
 * $Id: install.c 38415 2005-02-03 20:37:04Z theller $
 */

#define UNICODE

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

static PyObject *CreateShortcut(PyObject *self, PyObject *args)
{
    Py_UNICODE *path; /* path and filename */
    Py_UNICODE *description;
    Py_UNICODE *filename;

    Py_UNICODE *arguments = NULL;
    Py_UNICODE *iconpath = NULL;
    int iconindex = 0;
    Py_UNICODE *workdir = NULL;

    IShellLink *pShellLink = NULL;
    IPersistFile *pPersistFile = NULL;

    HRESULT hres;

    hres = CoInitialize(NULL);
    if (FAILED(hres)) {
        PyErr_Format(PyExc_OSError,
                       "CoInitialize failed, error 0x%x", hres);
        goto error;
    }

    if (!PyArg_ParseTuple(args, "uuu|uuui",
                          &path, &description, &filename,
                          &arguments, &workdir, &iconpath, &iconindex)) {
        return NULL;
    }

    hres = CoCreateInstance(CLSID_ShellLink, NULL,
                          CLSCTX_INPROC_SERVER,
                          IID_IShellLink,
                          (void **)&pShellLink);
    if (FAILED(hres)) {
        PyErr_Format(PyExc_OSError,
                       "CoCreateInstance failed, error 0x%x", hres);
        goto error;
    }

    hres = pShellLink->QueryInterface(IID_IPersistFile, (void**)&pPersistFile);
    if (FAILED(hres)) {
        PyErr_Format(PyExc_OSError,
                       "QueryInterface(IPersistFile) error 0x%x", hres);
        goto error;
    }


    hres = pShellLink->SetPath(path);
    if (FAILED(hres)) {
        PyErr_Format(PyExc_OSError,
                       "SetPath() failed, error 0x%x", hres);
        goto error;
    }

    hres = pShellLink->SetDescription(description);
    if (FAILED(hres)) {
        PyErr_Format(PyExc_OSError,
                       "SetDescription() failed, error 0x%x", hres);
        goto error;
    }

    if (arguments) {
        hres = pShellLink->SetArguments(arguments);
        if (FAILED(hres)) {
                PyErr_Format(PyExc_OSError,
                               "SetArguments() error 0x%x", hres);
                goto error;
        }
    }

    if (iconpath) {
        hres = pShellLink->SetIconLocation(iconpath, iconindex);
        if (FAILED(hres)) {
                PyErr_Format(PyExc_OSError,
                               "SetIconLocation() error 0x%x", hres);
                goto error;
        }
    }

    if (workdir) {
        hres = pShellLink->SetWorkingDirectory(workdir);
        if (FAILED(hres)) {
                PyErr_Format(PyExc_OSError,
                               "SetWorkingDirectory() error 0x%x", hres);
                goto error;
        }
    }

    hres = pPersistFile->Save(filename, TRUE);
    if (FAILED(hres)) {
        PyObject *fn = PyUnicode_FromUnicode(filename, wcslen(filename));
        if (fn) {
            PyObject *msg = PyUnicode_FromFormat(
                        "Failed to create shortcut '%U' - error 0x%x",
                        fn, hres);
            if (msg) {
                PyErr_SetObject(PyExc_OSError, msg);
                Py_DECREF(msg);
            }
            Py_DECREF(fn);
        }
        goto error;
    }

    pPersistFile->Release();
    pShellLink->Release();

    CoUninitialize();
    Py_RETURN_NONE;

  error:
    if (pPersistFile) {
        pPersistFile->Release();
    }
    if (pShellLink) {
        pShellLink->Release();
    }

    CoUninitialize();
    return NULL;
}

PyMethodDef meth[] = {
    {"create_shortcut", CreateShortcut, METH_VARARGS,
        "winshortcut.create_shortcut(path, description, filename,\n"
        "                  arguments=u\"\", workdir=None, iconpath=None,\n"
        "                  iconindex=0)\n"
        "\n"
        "  Creates a shortcut ``filename`` (a .lnk file), whose\n"
        "  target path is ``path``. All the input strings must be\n"
        "  unicode.\n"
        "\n"
        "  >>>winshortcut.create_shortcut(\"C:\\Target\\Path\\File.txt\",\n"
        "                                 \"Shortcut description\",\n"
        "                                 \"C:\\Shortcut\\Path\\Shortcut.lnk\"\n"},
    {NULL, NULL}
};

#if PY_VERSION_HEX >= 0x03000000
static struct PyModuleDef winshortcutmodule = {
   PyModuleDef_HEAD_INIT,
   "winshortcut",
   NULL, /* module documentation */
   -1,
   meth
};

PyMODINIT_FUNC
PyInit_winshortcut(void)
{
    return PyModule_Create(&winshortcutmodule);
}
#else
void initwinshortcut(void)
{
    Py_InitModule("winshortcut", meth);
}
#endif
