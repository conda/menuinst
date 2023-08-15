# Getting started

`menuinst` can be used to create shortcuts or menu items across operating systems.
It's designed to integrate nicely with `conda` packages,
but it can be used without it to an extent via its Python API (see below).

<!-- NOTE: General Python support will be added. This section will be rephrased then -->


## Installation

`menuinst` is usually installed along with `conda` in the `base` environment.
So, in most cases, you won't have to do much. For other environments, you can do:

```console
$ conda install "menuinst>=2"
```

## Usage

Currently, there is no CLI. This is being worked on, but for now you can use the Python API:

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
