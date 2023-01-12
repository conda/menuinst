# Define your own shortcuts

`menuinst` takes JSON configuration files as its input.
The minimal structure is a dictionary with four keys

- `$schema`: The JSON-schema standard version
- `$id`: The version of the menuinst configuration, as a JSON schema URL
- `menu_name`: The name for this group of menu items
- `menu_items`: A list of dictionaries, each defining the settings for one shortcut / menu item. Each menu item must define, at least, the following keys:
    - `name`: The name for this specific shortcut.
    - `command`: A list of strings detailing how to launch the application.
    - `platforms`: A dictionary with up to three keys. All of them are optional but you must at least define one. The presence of a key with a non-`null` value enables the shortcut for that platform. If you don't include any, shortcuts will not be created. Available keys are:
        - `linux`
        - `osx`
        - `win`

## Minimal example 

A minimal example to launch Python's `turtle` module would be:

```json
{
    "$schema": "https://json-schema.org/draft-07/schema",
    "$id": "https://schemas.conda.io/menuinst-1.schema.json",
    "menu_name": "Python {{ PY_VER }}",
    "menu_items": [
        {
            "name": "Launch Turtle",
            "command": ["python", "-m", "turtle"],
            "platforms": {
                "linux": {},
                "osx": {},
                "win": {},
            }
        }
    ]
}
```

This is not using any customization options or advanced features.
It's the bare minimum to make it work: a name, the command, and the target platforms.

If you want to learn more, check this reference for full details on the available fields and settings for each platform.
The JSON configurations follow a well-defined schema documented at {ref}`schema`.

```{tip}
Note how the `menu_name` is using a placeholder `{{ PY_VER }}`.
`menuinst` supports Jinja-like variables. 
The full list of available placeholders is available at {ref}`placeholders`.
```

## Integrate with `conda` packages

To enable the native `conda` integrations, instruct the `conda-build` scripts to place the `menuinst` JSON configuration files in `$PREFIX/Menu`.

On Linux and macOS this usually looks like:

```bash
# On your build.sh
mkdir -p "${PREFIX}/Menu"
cp "${RECIPE_DIR}/menu.json" "${PREFIX}/Menu/${PKG_NAME}_menu.json"
```

For Windows:

```batch
:: On bld.bat
mkdir "%PREFIX%\Menu"
copy /Y "%RECIPE_DIR%\menu.json" "%PREFIX%\Menu\%PKG_NAME%_menu.json"
```