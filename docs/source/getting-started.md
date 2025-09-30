# Getting started

`menuinst` can be used to create shortcuts or menu items across operating systems.
It's designed to integrate nicely with `conda` packages,
but it can be used without it to an extent via its CLI and Python API (see below).

<!-- NOTE: General Python support will be added. This section will be rephrased then -->


## Installation

`menuinst` is usually installed along with `conda` in the `base` environment.
So, in most cases, you won't have to do much. For other environments, you can do:

```console
$ conda install "menuinst>=2"
```

## Usage

### The `menuinst` CLI

`menuinst` provides a CLI that can be used to install shortcuts:

```shell
usage: menuinst [-h] --prefix PREFIX (--install [PKG ...] | --remove [PKG ...]) [--root-prefix ROOT_PREFIX]

options:
  -h, --help            show this help message and exit
  --prefix PREFIX       The prefix containing the shortcuts metadate inside `Menu`
  --install [PKG ...]   create menu items for the given metadata JSON files or packages; if none are given, create menu
                        items for all packages in the prefix
  --remove [PKG ...]    remove menu items for the given metadata JSON files or packages; if none are given, remove menu
                        items for all packages in the prefix
  --root-prefix ROOT_PREFIX
                        The menuinst base/root prefix
```

The CLI will look for [metadata files](./defining-shortcuts) inside the directory `${PREFIX}/Menu`.
`PKG` is a set of metadata file names.

For example, if `${PREFIX}/Menu` contains the file `package_menu.json`, its shortcuts can be
installed with:

```shell
menuinst --prefix ${PREFIX} --install package_menu.json
```

Alternatively, the package name of the `conda` package can be used:

```shell
menuinst --prefix ${PREFIX} --install package
```

If `PKG` is not set, all menu items in the prefix are installed/removed.

### As an API

The `menuinst` package can be used as an API:

```python
from menuinst.api import install
install("path/to/menu.json")
```

Or from the terminal:

```shell
$ python -c "from menuinst.api import install; install('path/to/menu.json')"
```

```{seealso}
Check {doc}`conda` for more information about using `menuinst` from `conda` packages.
```
