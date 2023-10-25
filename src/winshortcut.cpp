
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
#include <propvarutil.h>
#include <propkey.h>
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
    PyObject *py_path; /* path and filename */
    wchar_t *path;
    PyObject *py_description;
    wchar_t *description;
    PyObject *py_filename;
    wchar_t *filename;

    PyObject *py_arguments = NULL;
    PyObject *py_iconpath = NULL;
    int iconindex = 0;
    PyObject *py_workdir = NULL;
    PyObject *py_app_id = NULL;

    IShellLink *pShellLink = NULL;
    IPersistFile *pPersistFile = NULL;
    IPropertyStore *pPropertyStore = NULL;

    PROPVARIANT pv;
    HRESULT hres;

    hres = CoInitialize(NULL);
    if (FAILED(hres)) {
        PyErr_Format(PyExc_OSError,
                       "CoInitialize failed, error 0x%x", hres);
        goto error;
    }

    if (!PyArg_ParseTuple(args, "UUU|UUUiU",
                          &py_path, &py_description, &py_filename,
                          &py_arguments, &py_workdir, &py_iconpath, &iconindex, &py_app_id)) {
        goto error;
    }

    path = PyUnicode_AsWideCharString(py_path, NULL);
    if (path == NULL) {
        goto error;
    }
    description = PyUnicode_AsWideCharString(py_description, NULL);
    if (description == NULL) {
        goto error;
    }
    filename = PyUnicode_AsWideCharString(py_filename, NULL);
    if (filename == NULL) {
        goto error;
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

    if (py_arguments) {
        wchar_t *arguments = PyUnicode_AsWideCharString(py_arguments, NULL);
        if (arguments == NULL) {
            goto error;
        }
        hres = pShellLink->SetArguments(arguments);
        if (FAILED(hres)) {
                PyErr_Format(PyExc_OSError,
                               "SetArguments() error 0x%x", hres);
                PyMem_Free(arguments);
                goto error;
        }
        PyMem_Free(arguments);
    }

    if (py_iconpath) {
        wchar_t *iconpath = PyUnicode_AsWideCharString(py_iconpath, NULL);
        if (iconpath == NULL) {
            goto error;
        }
        hres = pShellLink->SetIconLocation(iconpath, iconindex);
        if (FAILED(hres)) {
                PyErr_Format(PyExc_OSError,
                               "SetIconLocation() error 0x%x", hres);
                PyMem_Free(iconpath);
                goto error;
        }
        PyMem_Free(iconpath);
    }

    if (py_workdir) {
        wchar_t *workdir = PyUnicode_AsWideCharString(py_workdir, NULL);
        if (workdir == NULL) {
            goto error;
        }
        hres = pShellLink->SetWorkingDirectory(workdir);
        if (FAILED(hres)) {
            PyErr_Format(PyExc_OSError,
                            "SetWorkingDirectory() error 0x%x", hres);
            PyMem_Free(workdir);
            goto error;
        }
        PyMem_Free(workdir);
    }

    if (py_app_id) {
        wchar_t *app_id = PyUnicode_AsWideCharString(py_app_id, NULL);
        if (app_id == NULL) {
            goto error;
        }
        hres = pShellLink->QueryInterface(IID_PPV_ARGS(&pPropertyStore));
        if (FAILED(hres)) {
            PyErr_Format(PyExc_OSError,
                           "QueryInterface(IPropertyStore) error 0x%x", hres);
            goto error;
        }
        hres = InitPropVariantFromString(app_id, &pv);
        if (FAILED(hres)) {
            PyErr_Format(PyExc_OSError,
                           "InitPropVariantFromString() error 0x%x", hres);
            goto error;
        }
        PyMem_Free(app_id);
        pPropertyStore->SetValue(PKEY_AppUserModel_ID, pv);
        pPropertyStore->Commit();
        PropVariantClear(&pv);
        pPropertyStore->Release();
    }

    hres = pPersistFile->Save(filename, TRUE);
    if (FAILED(hres)) {
        PyObject *fn = PyUnicode_FromWideChar(filename, wcslen(filename));
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

    PyMem_Free(path);
    PyMem_Free(description);
    PyMem_Free(filename);

    Py_XDECREF(py_path);
    Py_XDECREF(py_description);
    Py_XDECREF(py_filename);
    Py_XDECREF(py_arguments);
    Py_XDECREF(py_iconpath);
    Py_XDECREF(py_workdir);
    Py_XDECREF(py_app_id);

    CoUninitialize();
    Py_RETURN_NONE;

  error:
    if (pPersistFile) {
        pPersistFile->Release();
    }
    if (pShellLink) {
        pShellLink->Release();
    }
    if (pPropertyStore) {
        pPropertyStore->Release();
    }

    PyMem_Free(path);
    PyMem_Free(description);
    PyMem_Free(filename);
    
    Py_XDECREF(py_path);
    Py_XDECREF(py_description);
    Py_XDECREF(py_filename);
    Py_XDECREF(py_arguments);
    Py_XDECREF(py_iconpath);
    Py_XDECREF(py_workdir);
    Py_XDECREF(py_app_id);

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
