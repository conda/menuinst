# Getting started

`menuinst` can be used to create shortcuts or menu items across operating systems.
It's designed to integrate nicely with `conda` packages, but it can be used without it to an extent.

## Installation

`menuinst` needs to be installed along with `conda`, usually in the `base` environment.
So, in most cases, you won't have to do much. For other environments, you can do:

```console
$ conda install "menuinst>=2"
```

## Usage and configuration

```{tip}
If you want to learn how to create shortcuts for `conda` packages you are building and maintaining, check {ref}`defining-shortcuts`.
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

## Removing shortcuts

The shortcuts created by `menuinst` will be removed automatically by `conda` when you uninstall the associated package from an environment.

```{warning}
`conda` has a known issue with environment removals. If you run `conda env remove -n <YOUR_ENV>`, the pre-uninstall actions will NOT be executed, which means that `menuinst` won't be invoked and the shortcut artifacts won't be removed. To clear an environment fully in a clean way, you'd need to run `conda remove -n <YOUR_ENV> --all`.
```
