# menuinst: cross platform menu item installation

This package provides cross platform menu item installation for `conda` packages.

If a conda package ships a [menuinst JSON document][reference] under `$PREFIX/Menu`, `conda` will invoke
`menuinst` to process the JSON file and install the menu items in your operating system.
The menu items are removed when the package is uninstalled.

The following formats are supported:

- Windows: `.lnk` files in the Start menu. Optionally, also in the Desktop and Quick Launch.
- macOS: `.app` bundles in the Applications folder.
- Linux: `.desktop` files as defined in the XDG standard.

## Documentation

Documentation is available at https://conda.github.io/menuinst/.

## History

This package was originally developed and maintained by Enthought under the name AppInst. The name
appinst is a rename of what used to be called 'wininst'.

`menuinst` v1 was only supported on Windows.  Legacy code existed in v1 for Linux and OS X - use at your own risk.  It may mess up your menus.

`menuinst` v2 is a backwards-compatible rewrite to address cross-platform compatibility under a
unified JSON schema, as discussed in [CEP-11][CEP-11]. The Windows bits of the v1 code are still
available under the `menuinst._legacy` subpackage.

## Build status

| [![Build status](https://github.com/conda/menuinst/actions/workflows/tests.yml/badge.svg)](https://github.com/conda/menuinst/actions/workflows/tests.yml) [![Docs status](https://github.com/conda/menuinst/actions/workflows/docs.yml/badge.svg)](https://github.com/conda/menuinst/actions/workflows/docs.yml) [![codecov](https://codecov.io/gh/conda/menuinst/branch/main/graph/badge.svg)](https://codecov.io/gh/conda/menuinst) [![pre-commit.ci status](https://results.pre-commit.ci/badge/github/conda/menuinst/main.svg)](https://results.pre-commit.ci/latest/github/conda/menuinst/main)  | [![Anaconda-Server Badge](https://anaconda.org/conda-canary/menuinst/badges/latest_release_date.svg)](https://anaconda.org/conda-canary/menuinst) |
| --- | :-: |
| [`conda install defaults::menuinst`](https://anaconda.org/anaconda/menuinst) | [![Anaconda-Server Badge](https://anaconda.org/anaconda/menuinst/badges/version.svg)](https://anaconda.org/anaconda/menuinst) |
| [`conda install conda-forge::menuinst`](https://anaconda.org/conda-forge/menuinst) | [![Anaconda-Server Badge](https://anaconda.org/conda-forge/menuinst/badges/version.svg)](https://anaconda.org/conda-forge/menuinst) |
| [`conda install conda-canary/label/dev::menuinst`](https://anaconda.org/conda-canary/menuinst) | [![Anaconda-Server Badge](https://anaconda.org/conda-canary/menuinst/badges/version.svg)](https://anaconda.org/conda-canary/constructor) |

[CEP-11]: https://github.com/conda-incubator/ceps/blob/3da0fb0ece/cep-11.md
[reference]: https://conda.github.io/menuinst/reference/
