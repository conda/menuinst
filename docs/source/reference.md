# Reference

## JSON configuration overview

This is an auto-generated overview of all the possible settings each `menuinst` JSON file can include.
Note that each platform sub-dict can override top-level values if required.
See Schema below for more details.

{{ default_schema_json }}

(schema)=

## Configuration schema

```{eval-rst}
.. autopydantic_model:: menuinst._schema.MenuInstSchema
.. autopydantic_model:: menuinst._schema.MenuItem
.. autopydantic_model:: menuinst._schema.Platforms
.. autopydantic_model:: menuinst._schema.Linux
.. autopydantic_model:: menuinst._schema.MacOS
    :member-order: groupwise

.. autopydantic_model:: menuinst._schema.Windows
```

(placeholders)=

## Placeholders

The JSON configuration files support several placeholders if surrounded with spaced double curly braces: `{{ variable }}`.
Note these are _not_ Jinja templates. It just follows the same syntax, but accepts no transformations. Only variable names are accepted!

### General placeholders

Variable | Value
---------|-------
`BASE_PREFIX` | Path to the base Python location. In `conda` terms, this is the `base` environment
`DISTRIBUTION_NAME` | Name of the base prefix directory; e.g. if `BASE_PREFIX` is `/opt/my-project`, this is `my-project`.
`PREFIX` | Path to the target Python location. In `conda` terms, this is the path to the environment that contains the JSON file for this menu item. In some cases, it might be the same as `BASE_PREFIX`.
`ENV_NAME` | Same as `DISTRIBUTION_NAME`, but for `PREFIX`.
`PYTHON` | Path to the `python` executable in `PREFIX`.
`BASE_PYTHON` | Path to the `python` executable in `BASE_PREFIX`.
`MENU_DIR` | Path to the `Menu` directory in `PREFIX`.
`MENU_ITEM_LOCATION` | Path to the main menu item artifact once installed. On Linux, this is the path to the `.desktop` file, on macOS it is the path to the `.app` directory, and on Windows it is the path to the Start Menu `.lnk` file.
`BIN_DIR` | Path to the `bin` (Unix) or `Library/bin` (Windows) directories in `PREFIX`.
`PY_VER` | Python `major.minor` version in `PREFIX`.
`SP_DIR` | Path to Python's `site-packages` directory in `PREFIX`.
`HOME` | Path to the user directory (`~`).
`ICON_EXT` | Extension of the icon file expected by each platform. `png` in Linux, `icns` in macOS, and `ico` in Windows. Note the dot is _not_ included.

### macOS placeholders

Variable | Value
---------|-------
`PYTHONAPP` | Path to the `python` executable installed in `PREFIX`, assuming the `python.app` conda package is installed. Equivalent to `{{ PREFIX }}/python.app/Contents/MacOS/python`.

### Windows placeholders

Variable | Value
---------|-------
`SCRIPTS_DIR` | Path to the `Scripts` directory in `PREFIX`.
`BASE_PYTHONW` | Path to the `pythonw.exe` executable in `BASE_PREFIX`.
`PYTHONW` | Path to the `pythonw.exe` executable in `PREFIX`.
