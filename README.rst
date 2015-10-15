===============================================
menuinst: cross platform menu item installation
===============================================

This package is was originally developed and maintained by Enthought
under the name AppInst.  The name appinst is a rename of what used
to be called 'wininst'.

Usage on Windows:
=================

This application is used by Conda to create shortcuts on a wide variety of
systems.  To create shortcuts, you'll need to add a menu entry file named
**menu-windows.json** to your conda recipe.  An example file's contents would be:

.. code-block:: javascript

    [
        {
            "name": "IPython (Py __PY_VER__)",
            "pyscript": "${PYTHON_SCRIPTS}/ipython-script.py",
            "icon": "${MENU_DIR}/IPython.ico"
        }
    ]

There can be more than one dictionary per JSON file (one per shortcut).

**Note:** two fields are required for each shortcut: "name" and some action type.

By default, this puts your shortcut under the Anaconda menu entry.  To create your own folder, you can add additional keys:

.. code-block:: javascript

    {
        "menu_name": "World",
        "menu_items":
            [
                {
                    "name": "Hello World",
                    "pyscript": "${PYTHON_SCRIPTS}/helloworld-script.py"
                }
            ]
    }
   

Make sure that you copy the menu-windows.json file in your blt.bat script:

.. code-block:: 

    copy menu-windows.json %MENU_DIR%\

Supported action types on Windows:
----------------------------------

  * **pyscript**: Run supplied python script with interpreter on PATH
  * **pywscript**: Run supplied python script with pythonw interpreter on PATH
  * **webbrowser**: Open system default web browser to supplied link
  * **script**: Execute supplied argument (e.g. batch file, executable, etc.)

Making icons accessible:
------------------------

To make your desired icon accessible, copy it in your bld.bat file to %MENU_DIR%, which conda defines.

.. code-block::

    copy %RECIPE_DIR%\IPython.ico %MENU_DIR%\
