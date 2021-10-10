.. _conda-recipes:

Menus in conda recipes
======================

If your package contains a JSON file under the ``Menu/`` directory,
``conda`` will detect it and process it with ``menuinst``.
This JSON file contains all the instructions that ``menuinst`` needs
to create a menu item in any of the supported platforms.

.. note::

    Check :ref:`configuration` for the required content in your JSON
    files.


As a result, you can use the build scripts in the conda recipe
to copy the JSON menu files into the ``${PREFIX}/Menu`` (Unix)
or ``%PREFIX%\Menu`` (Windows) folder when building conda packages
using ``conda build``.

Example ``bld.bat``:

.. code-block:: shell

    if not exist "%PREFIX%\Menu" mkdir "%PREFIX%\Menu"
    copy "%RECIPE_DIR%\menu-windows.json" "%PREFIX%\Menu"
    copy "%RECIPE_DIR%\app.ico" "%PREFIX%\Menu"

    "%PYTHON%" setup.py install
    if errorlevel 1 exit 1


Example ``build.sh``:

.. code-block:: shell

    #!/bin/bash
    set -euxo pipefail

    mkdir -p "$PREFIX/Menu"
    if [[ $target_platform == osx-* ]]; then
        cp "$RECIPE_DIR/menu-osx.json" "$PREFIX/Menu"
        cp "$RECIPE_DIR/app.icns" "$PREFIX/Menu"
    else
        cp "$RECIPE_DIR/menu-linux.json" "$PREFIX/Menu"
        cp "$RECIPE_DIR/app.svg" "$PREFIX/Menu"
    fi

    "$PYTHON" -m pip install . || exit 1

