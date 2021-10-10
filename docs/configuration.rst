.. _configuration:

Configuration files
===================

``menuinst`` creates menu items using the information specified
in carefully placed JSON files. The structure and content of
these JSON files varies slightly across operating systems, as
detailed below.

Windows
-------

.. code-block:: javascript

    {
        "menu_name": "World", // the name of the Start menu folder
        "menu_items":
            [
                {   // script to call after pseudo-activating the environment
                    "script": "${PREFIX}/some_command.exe",
                    "scriptarguments": ["list", "of", "arguments"],
                    // The following options can be applied to any shortcut type:
                    "name": "Hello World",
                    "workdir": "${PREFIX}",
                    "icon": "${MENU_DIR}/app.ico",
                    "desktop": true,  // Also create desktop shortcut
                    "quicklaunch": true  // Also create "Quick Launch" bar shortcut
                },
                {   // launch script with pythonw.exe
                    "pywscript": "${PYTHON_SCRIPTS}/helloworld_ui-script.py"
                },
                {   // launch script with python.exe
                    "pyscript": "${PYTHON_SCRIPTS}/helloworld-script.py"
                },
                {   // open a website
                    "webbrowser": "https://hello.com"
                },
                {   // execute this command as is, no pseudo-activation
                    "system": "path to executable.  No environment modification is done.",
                    "scriptarguments": ["list", "of", "arguments"]
                }
            ]
    }


Available variables include:

- ``${PREFIX}``: Python environment prefix.
- ``${ROOT_PREFIX}``: Python environment prefix of root (conda or otherwise) installation.
- ``${PYTHON_SCRIPTS}``: Scripts folder in Python environment, ``${PREFIX}/Scripts``.
- ``${MENU_DIR}``: Folder for menu config and icon files, ``${PREFIX}/Menu``.
- ``${PERSONALDIR}``: Not sure.
- ``${USERPROFILE}``: User's home folder.
- ``${ENV_NAME}``: The environment in which this shortcut lives.
- ``${DISTRIBUTION_NAME}``: The name of the folder of the root prefix, for example "Miniconda"
  if distribution installed at ``C:\Users\Miniconda``.
- ``${PY_VER}``: The Python major version only. This is taken from the root prefix.
  Used generally for placing shortcuts under a menu of a parent installation.
- ``${PLATFORM}``: one of (32-bit) or (64-bit). This is taken from the root prefix.
  Used generally for placing shortcuts under a menu of a parent installation.

On Windows, ``menuinst`` uses a small C program to call the Windows
libraries that will end up creating the actual shortcut. The commands run by
``script``, ``pyscript`` and ``pywscript`` are first passed through an initialization
script (``cwp.py``) that pre-activates the environment by including certain directories in PATH
and then calls a subprocess with the user specified command:

More specifically:

``script``::

    $ROOT_PREFIX/python.exe cwp.py $PREFIX [script] [scriptarguments]

``pyscript``::

    $ROOT_PREFIX/python.exe cwp.py $PREFIX $PREFIX/python.exe [pyscript]

``pywscript``::

    $ROOT_PREFIX/pythonw.exe cwp.py $PREFIX $PREFIX/pythonw.exe [pywscript]


Linux
-----

On Linux, ``menuinst`` follows the Free Desktop standards, which specify a ``.desktop``
file format. The allowed configuration is:

.. code-block:: javascript

    {
        "menu_name": "World",
        "menu_items":
            [
                {
                    "cmd": ["/usr/bin/helloworld", "arg1", "..", "argn"],
                    // The following options can be applied to any shortcut type:
                    "id": "id1",  // For shortcut file name, becomes "World_id1"
                    "name": "Hello World",
                    "comment": "Hello World application",
                    "terminal": true,
                    "icon": "path/to/icon"
                },
                {
                    "cmd": ["{{FILEBROWSER}}", "~/HelloWorld.txt"]
                },
                {
                    "cmd": ["{{WEBBROWSER}}", "https://hello.com"]
                }
            ]
    }

The available placeholders ``{{FILEBROWSER}}`` and ``{{WEBBROWSER}}``
will be replaced by the adequate file browser and web browser available
in the target platform, respectively.


MacOS
-----

On MacOS, ``menuinst`` will create an Application folder (``your_package.app``),
which will contain a shell script running the requested command.

.. code-block:: javascript

    {
        "menu_name": "World",
        "menu_items":
            [
                {
                    "cmd": "${BIN_DIR}/helloworld",
                    "name": "Hello World",
                    "icns": "${MENU_DIR}/app.icns"
                }
            ]
    }

Available variables include:

 - ``${BIN_DIR}``: {prefix}/bin
 - ``${MENU_DIR}``: {prefix}/Menu

Note that ``${PREFIX}`` is not available! You would have to do ``${BIN_DIR}/..``.