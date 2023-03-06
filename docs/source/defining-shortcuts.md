# Define your own shortcuts

`menuinst` takes JSON configuration files as its input.
The minimal structure is a dictionary with four keys

- `$schema`: The JSON-schema standard version
- `$id`: The version of the menuinst configuration, as a JSON schema URL
- `menu_name`: The name for this group of menu items
- `menu_items`: A list of dictionaries, each defining the settings for one shortcut / menu item. Each menu item must define, at least, the following keys (see {class}`MenuItem schema <menuinst._schema.MenuItem>` for more details):
    - `name`: The name for this specific shortcut.
    - `command`: A list of strings detailing how to launch the application.
    - `platforms`: A dictionary with up to three keys. All of them are optional but you must at least define one. The presence of a key with a non-`null` value enables the shortcut for that platform. If you don't include any, shortcuts will not be created. Available keys are:
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
                "win": {},
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

This is not using any customization options or advanced features.
It's the bare minimum to make it work: a name, the command, and the target platforms.

## Associate your shortcut with file types and URL protocols

### File types

Each operating system has a slightly different way of associating a file type to a given shortcut.
Unix systems have the notion of MIME types, while Windows relies more on file name extensions.

* On Linux, use the `MimeType` option.
  Remember to add the `%f` (single file) or `%F` (several files) placeholders to your command
  so the URLs are passed adequately.
* On macOS, use `CFBundleDocumentTypes`. Requires no placeholder. The opened document will be automatically passed as an argument.
* On Windows, use `file_extensions`. Remember to add the `%1` or `%*` placeholders to your command
  so the path of the opened file(s) is passed adequately.


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
            "command": ["{{ PREFIX }}/bin/my_csv_reader.py"],
            "icon": "{{ MENU_DIR }}/my_csv_reader.{{ ICON_EXT }}",
            "platforms": {
                "linux": {
                    "command": ["{{ PREFIX }}/bin/my_csv_reader.py", "%f"],
                    "MimeType": ["text/csv"]
                },
                "macos": {
                    "CFBundleDocumentTypes": [
                        {
                            "CFBundleTypeIconFile": "{{ MENU_DIR }}/my_csv_reader",
                            "CFBundleTypeName": "my-csv-reader.csv",
                            "CFBundleTypeRole": "Viewer",
                            "LSItemContentTypes": ["public.comma-separated-values-text"],
                            "LSHandlerRank": "Default"
                        }
                    ]
                },
                "windows": {
                    "command": ["{{ SCRIPTS_DIR }}/my_csv_reader.py", "%1"],
                    "file_extensions": [".csv"]
                }
            }
        }
    ]
}
```

### URL protocols

Each operating system has a slightly different way of associating a URL protocol to a given shortcut.

* On Linux, you must use the `MimeType` option too.
  Use the `x-scheme-handler/your-protocol-here` syntax.
  Remember to add the `%u` (single URL) or `%U` (several URLs) placeholders to your command
  so the URLs are passed adequately.
* On macOS, use `CFBundleURLTypes`. Requires no placeholder. The URL will be dispatched via events. Right now, the .app launcher/forwarder doesn't know about the Apple events involved in this, so **it will not work**. WIP.
* On Windows, use `url_protocols`. Remember to add the `%1` or `%*` placeholders to your command
  so the URLs are passed adequately.


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
                "macos": {
                    "CFBundleURLTypes": [
                        {
                            "CFBundleURLIconFile": "{{ MENU_DIR }}/my_protocol_handler",
                            "CFBundleURLName": "my-protocol-handler.menuinst.does-not-work-yet",
                            "CFBundleTypeRole": "Viewer",
                            "CFBundleURLSchemes": ["menuinst"]
                        }
                    ]
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
