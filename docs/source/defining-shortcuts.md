# Define your own shortcuts

`menuinst` takes JSON configuration files as its input. The minimal structure is a dictionary with
four keys

- `$schema`: The JSON-schema standard version
- `$id`: The version of the menuinst configuration, as a JSON schema URL
- `menu_name`: The name for this group of menu items
- `menu_items`: A list of dictionaries, each defining the settings for one shortcut / menu item.
  Each menu item must define, at least, the following keys (see {class}`MenuItem schema <menuinst._schema.MenuItem>`
  for more details):
    - `name`: The name for this specific shortcut.
    - `command`: A list of strings detailing how to launch the application.
    - `platforms`: A dictionary with up to three keys. All of them are optional but you must at
      least define one. The presence of a key with a non-`null` value enables the shortcut for that
      platform. If you don't include any, shortcuts will not be created. Available keys are:
        - `linux` - see {class}`Linux schema <menuinst._schema.Linux>`
        - `osx`- see {class}`MacOS schema <menuinst._schema.MacOS>`
        - `win`- see {class}`Windows schema <menuinst._schema.Windows>`

```{warning}
`menuinst` will overwrite existing shortcuts on Linux and Windows, so `menu_name` and `name` must be chosen accordingly.

MacOS apps, however, will not be overwritten. Instead, `menuinst` will abort when an app with the same name exists.
```

```{seealso}
If you want to learn more, check the {doc}`reference` for full details on the available fields and settings for each platform.
The JSON configurations follow a well-defined schema documented at {ref}`schema`.
```

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
        "win": {}
      }
    }
  ]
}
```

```{tip}
Note how the `menu_name` is using a placeholder `{{ PY_VER }}`.
`menuinst` supports Jinja-like variables.
The full list of available placeholders is available at {ref}`placeholders`.
```

This is not using any customization options or advanced features. It's the bare minimum to make it
work: a name, the command, and the target platforms.

## Specifying different shortcut names for base and non-base environments

If environments are supported, different naming schemes can be specified for installations into
the base environment and non-base environments.
To do this, the `name` property must be a dictionary with the keys `target_environment_is_base`
and `target_environment_is_not_base` for installations into the base and non-base environment,
respectively.


The example below creates a shortcut called with the name "Launch Turtle" if installed into the
base environment. If installed into an environment called, e.g., `turtle`, the name of the shortcut
is "Launch Turtle (turtle)". This was the default behavior of `menuinst` version 1.

```json
{
  "$schema": "https://json-schema.org/draft-07/schema",
  "$id": "https://schemas.conda.io/menuinst-1.schema.json",
  "menu_name": "Python {{ PY_VER }}",
  "menu_items": [
    {
      "name": {
        "target_environment_is_base": "Launch Turtle",
        "target_environment_is_not_base": "Launch Turtle ({{ ENV_NAME }})"
      }
      "command": ["python", "-m", "turtle"],
      "activate": true,
      "platforms": {
        "linux": {},
        "osx": {},
        "win": {}
      }
    }
  ]
}
```

## Associate your shortcut with file types and URL protocols

### File types

Each operating system has a slightly different way of associating a file type to a given shortcut.
Unix systems have the notion of MIME types, while Windows relies more on file name extensions.

- On Linux, use the `MimeType` option. Remember to add the `%f` (single file) or `%F` (several
  files) placeholders to your command so the paths are passed adequately. If you are defining a new
  MIME type, you must fill the `glob_patterns` field by mapping the new MIME type to the file
  extensions you want to associate with it.
- On Windows, use `file_extensions`. Remember to add the `%1` or `%*` placeholders to your command
  so the path of the opened file(s) is passed adequately.
- On macOS, use `CFBundleDocumentTypes`. Requires no placeholder. The opened document will be
  automatically passed as a regular command-line argument. The association happens via UTI strings
  (Uniform Type Identifiers). If you need UTIs not defined by Apple, use the
  `UTImportedTypeDeclarations` field if they are provided by other apps, or
  `UTExportedTypeDeclarations` if you are defining them yourself.

(macos-event-handler)=

:::{admonition} Event handlers in macOS
:class: note

On macOS, opened files are dispatched via system events. If your application knows how to handle
these events, then you don't need anything else. However, if your app is not aware of system
events, you need to set the `event_handler` field to define a logic that will forward the caught
files to your application (via sockets, API calls, `inotify` or any other inter-process communication
mechanism). [See `event_handler` example](https://github.com/conda/menuinst/blob/e992e76/tests/data/jsons/file_types.json#L35-L57).

When `event_handler` is set, `menuinst` will inject an additional launcher written in Swift to
handle the Apple events. The Swift runtime libraries are only guaranteed to be available on macOS
10.14.4 and later. If you need to support older versions of macOS, you will need to instruct your
users to install the Swift runtime libraries manually, available at
https://support.apple.com/kb/DL1998. You can add a dependency on `__osx>=10.14.4` on your conda
package if you wish to enforce it.
:::

:::{admonition} Dock blip on macOS
:class: tip

Note that setting `CFBundleTypeRole` will make the wrapper blip in the dock when the URL is
opened. If you don't want that, do not set it.
:::

A multi-platform example can be found at [`tests/data/jsons/file_types.json`](https://github.com/conda/menuinst/blob/main/tests/data/jsons/file_types.json).

### URL protocols

Each operating system has a slightly different way of associating a URL protocol to a given
shortcut.

- On Linux, you must use the `MimeType` option too. Use the `x-scheme-handler/your-protocol-here`
  syntax. Remember to add the `%u` (single URL) or `%U` (several URLs) placeholders to your command
  so the URLs are passed adequately.
- On Windows, use `url_protocols`. Remember to add the `%1` or `%*` placeholders to your command so
  the URLs are passed adequately.
- On macOS, use `CFBundleURLTypes`. Requires no placeholders. See
  {ref}`relevant note in File Types <macos-event-handler>`.

A multi-platform example can be found at [`tests/data/jsons/url_protocols.json`](https://github.com/conda/menuinst/blob/main/tests/data/jsons/url_protocols.json).

## Notes on Windows shortcuts

### Directories do not appear under All apps in the Start Menu

Directories defined by `menu_name` may not always appear in the Start Menu.
On Windows 11, directories are only shown if they contain more than one shortcut.
Otherwise, the shortcut will appear directly under "All apps".
This behavior is normal for Windows 11 - `menuinst` still creates the directories correctly.

### Migrating pywscript and pyscript to menuinst v2

`menuinst v1` contained `pywscript` and `pyscript` fields that allowed python scripts inside
a `conda` environment to be called.

```json
{
  "menu_name": "App",
  "menu_items": [
    {
      "name": "Launch App",
      "pywscript": "${PYTHON_SCRIPTS}/app-launcher.py"
    }
  ]
}
```

However, these wrappers just adjusted `PATH` and did not activate the `conda` environment
so that environment variables were unavailable.

These fields have been removed with `menuinst v2`. Instead, the environment should be activated
and the script executed directly.

```json
{
  "$schema": "https://json-schema.org/draft-07/schema",
  "$id": "https://schemas.conda.io/menuinst-1.schema.json",
  "name": "App",
  "menu_items": [
    "name": "Launch App"
    "description": "Launch App",
    "activate": true,
    "command": [
      "{{ PREFIX }}/pythonw.exe",
      "{{ SCRIPTS_DIR }}/app-launcher.py"
    ],
    "platforms": {
      "win": {
      }
    }
  ]
}
```

This will briefly open a terminal Window to launch the python instance.
If this flashing is not desired, `menuinst v1` behavior can be restored
by explicitly calling the wrapper:

```json
{
  "$schema": "https://json-schema.org/draft-07/schema",
  "$id": "https://schemas.conda.io/menuinst-1.schema.json",
  "name": "App",
  "menu_items": [
    "name": "Launch App"
    "description": "Launch App",
    "activate": true,
    "command": [
      "{{ BASE_PYTHONW }}",
      "{{ BASE_PREFIX }}/cwp.py",
      "{{ PREFIX }}",
      "{{ PYTHONW }}",
      "{{ SCRIPTS_DIR }}/app-launcher.py"
    ],
    "platforms": {
      "win": {
      }
    }
  ]
}
```
