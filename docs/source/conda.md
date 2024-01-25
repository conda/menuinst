# Integrations with conda

While it can be used as a Python library on its own,
`menuinst` has been designed to work closely with `conda`.

## Installing shortcuts from `conda` packages

```{tip}
If you want to learn how to create shortcuts for `conda` packages you are building and maintaining, check {doc}`defining-shortcuts`.
```

`menuinst` integrates natively with `conda`, so as an end user you don't need to do anything to enable it.
If a package is shipping a `menuinst`-compatible shortcut, it will be detected at installation time, and `conda` will invoke `menuinst` on its own.

If you want to change the default behavior, there are some command-line flags you can use:

- `--shortcuts` instructs `conda` to create shortcuts if present (default behavior).
- `--no-shortcuts` can be used to disable the creation of all shortcuts in that command.

These options can also be set in your `.condarc` configuration. Choose one of:

```yaml
shortcuts: true   # default
shortcuts: false  # equivalent to always using --no-shortcuts
```

```{note}
`mamba` has limited support for menuinst. For more information, follow these issues:

- https://github.com/mamba-org/mamba/issues/1316
- https://github.com/mamba-org/mamba/issues/923
```

### Removing shortcuts

The shortcuts created by `menuinst` will be removed automatically by `conda` when you uninstall the associated package from an environment.

```{warning}
`conda` has a known issue with environment removals. If you run `conda env remove -n <YOUR_ENV>`, the pre-uninstall actions will NOT be executed, which means that `menuinst` won't be invoked and the shortcut artifacts won't be removed. To clear an environment fully in a clean way, you'd need to run `conda remove -n <YOUR_ENV> --all`.
```

## Adding shortcuts to `conda` packages

To enable the native `conda` integrations, instruct the `conda-build` scripts to place the `menuinst` JSON configuration files in `$PREFIX/Menu`.


````{tabs}

```{code-tab} yaml meta.yaml (noarch)
build:
  noarch: python
  number: 0
  script:
    - mkdir -p "{{ PREFIX }}/Menu"
    - cp "{{ RECIPE_DIR }}/menu.json" "{{ PREFIX }}/Menu/{{ PKG_NAME }}_menu.json"
```

```{code-tab} bash build.sh (Linux and macOS)
mkdir -p "${PREFIX}/Menu"
cp "${RECIPE_DIR}/menu.json" "${PREFIX}/Menu/${PKG_NAME}_menu.json"
```

```{code-tab} batch bld.bat (Windows)
mkdir "%PREFIX%\Menu"
copy /Y "%RECIPE_DIR%\menu.json" "%PREFIX%\Menu\%PKG_NAME%_menu.json"
```
````

````{tip}
Use string substitution tools to automatically replace the version on your shortcuts:

With this JSON file:

```json
{
    "$schema": "https://json-schema.org/draft-07/schema",
    "$id": "https://schemas.conda.io/menuinst-1.schema.json",
    "menu_name": "my_application (__PKG_VERSION__)",
    "menu_items": ["..."]
}
```

Use `sed` like this:

```bash
$ sed "s/__PKG_VERSION__/${PKG_VERSION}/g" "${RECIPE_DIR}/menu.json" > "${PREFIX}/Menu/${PKG_NAME}_menu.json"
```
````

```{note}
On Windows, `menuinst` will add " (\{\{ ENV_NAME \}\})" to the shortcut name if the package is installed outside the base environment.
```
