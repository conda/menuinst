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
  automatically passed as a regular command-line argument. The file will be dispatched via events.
  You need to define the `event_handler` field to define a logic that will forward the caught files
  to your application (via sockets, API calls, inotify or any other inter-process communication
  mechanism) The association happens via UTI strings (Uniform Type Identifiers). If you need UTIs
  not defined by Apple, use the `UTImportedTypeDeclarations` field if they are provided by other
  apps, or `UTExportedTypeDeclarations` if you are defining them yourself.

:::{note}
On macOS, this feature uses an additional launcher written in Swift to handle the Apple events.
The Swift runtime libraries are only guaranteed to be available on macOS 10.14.4 and later.
If you need to support older versions of macOS, you will need to instruct your users to install
the Swift runtime libraries manually, available at https://support.apple.com/kb/DL1998.
You can add a dependency on `__osx>=10.14.4` on your conda package if you wish to enforce it.
:::


A multi-platform example:

```json
{
  "$schema": "https://json-schema.org/draft-07/schema",
  "$id": "https://schemas.conda.io/menuinst-1.schema.json",
  "menu_name": "File type handler example",
  "menu_items": [
    {
      "name": "My CSV Reader",
      "activate": true,
      "command": ["{{ PREFIX }}/bin/open_menuinst_files.py"],
      "icon": "{{ MENU_DIR }}/open_menuinst_files.{{ ICON_EXT }}",
      "platforms": {
        "linux": {
          "command": ["{{ PREFIX }}/bin/open_menuinst_files.py", "%f"],
          "MimeType": ["application/x-menuinst"],
          "glob_patterns": {
            "application/x-menuinst": ["*.menuinst"]
          }
        },
        "osx": {
          "CFBundleDocumentTypes": [
            {
              "CFBundleTypeName": "org.conda.menuinst.opener",
              "CFBundleTypeRole": "Viewer",
              "LSItemContentTypes": ["org.conda.menuinst.main-file-uti"],
              "LSHandlerRank": "Default"
            }
          ],
          "UTExportedTypeDeclarations": [
            {
              "UTTypeConformsTo": ["public.data", "public.content"],
              "UTTypeIdentifier": "org.conda.menuinst.main-file-uti",
              "UTTypeTagSpecification": [
                {
                  "public.filename-extension": ["menuinst"]
                }
              ]
            }
          ]
        },
        "windows": {
          "command": ["{{ SCRIPTS_DIR }}/open_menuinst_files.py", "%1"],
          "file_extensions": [".csv"]
        }
      }
    }
  ]
}
```

### URL protocols

Each operating system has a slightly different way of associating a URL protocol to a given
shortcut.

- On Linux, you must use the `MimeType` option too. Use the `x-scheme-handler/your-protocol-here`
  syntax. Remember to add the `%u` (single URL) or `%U` (several URLs) placeholders to your command
  so the URLs are passed adequately.
- On Windows, use `url_protocols`. Remember to add the `%1` or `%*` placeholders to your command so
  the URLs are passed adequately.
- On macOS, use `CFBundleURLTypes`. Requires no placeholders. The URL will be dispatched via
  events. You need to define the `event_handler` field to define a logic that will forward the
  caught URLs to your application (via sockets, API calls, inotify or any other inter-process
  communication mechanism). Note that setting `CFBundleTypeRole` will make the wrapper blip in the
  dock when the URL is opened. If you don't want that, do not set it.

:::{note}
On macOS, this feature uses an additional launcher written in Swift to handle the Apple events.
The Swift runtime libraries are only guaranteed to be available on macOS 10.14.4 and later.
If you need to support older versions of macOS, you will need to instruct your users to install
the Swift runtime libraries manually, available at https://support.apple.com/kb/DL1998.
You can add a dependency on `__osx>=10.14.4` on your conda package if you wish to enforce it.
:::

```json
{
  "$schema": "https://json-schema.org/draft-07/schema",
  "$id": "https://schemas.conda.io/menuinst-1.schema.json",
  "menu_name": "Protocol handler example",
  "menu_items": [
    {
      "name": "My custom menuinst:// handler",
      "activate": true,
      "command": ["{{ PREFIX }}/bin/my_protocol_handler.py"],
      "icon": "{{ MENU_DIR }}/my_protocol_handler.{{ ICON_EXT }}",
      "platforms": {
        "linux": {
          "command": ["{{ PREFIX }}/bin/my_protocol_handler.py", "%u"],
          "MimeType": ["x-scheme-handler/menuinst"]
        },
        "osx": {
          "command": [
            "{{ PREFIX }}/bin/my_protocol_handler.py",
            "--listen",
            "4444"
          ],
          "CFBundleURLTypes": [
            {
              "CFBundleURLIconFile": "{{ MENU_DIR }}/my_protocol_handler",
              "CFBundleURLName": "my-protocol-handler.menuinst.does-not-work-yet",
              "CFBundleURLSchemes": ["menuinst"]
            }
          ],
          "event_handler": "for i in 1 2 3 4 5; do echo \"$*\" | nc localhost 4444 && break || sleep 1; done"
        },
        "windows": {
          "command": ["{{ SCRIPTS_DIR }}/my_protocol_handler.py", "%1"],
          "url_protocols": ["menuinst"]
        }
      }
    }
  ]
}
```
