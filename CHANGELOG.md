[//]: # (current developments)

## 2.0.0 (2023-09-14)

### Enhancements

* Add support for file extension and URL protocol association on Windows. (#117)
* Add support for URL protocol and file type association in all operating systems. Adds tests and examples. (#118 via #119, #135)
* Add `app_user_model_id` field on Windows shortcuts to group taskbar icons together. (#127 via #133)
* Enable automatic elevation on Unix platforms too, and add tests. (#137 via #138, #139)
* Add recipe and CI workflow steps to build and upload canaries to `conda-canary`. (#144, #145, #149)
* Implement auto-elevation logic in Unix systems so it doesn't depend on pre-existing `.nonadmin` files. (#150 via #156)

### Bug fixes

* Ensure some v1-only import paths are still available for backwards compatibility. (#151)
* Do not capitalize `${DISTRIBUTION_NAME}` in v1-style `menuinst` JSON documents. (#153)

### Docs

* Create Sphinx-based documentation following community practices (constructor, conda-libmamba-solver). Absorbs and updates the existing info in wiki and non-deployed docs. (#112)
* Add development documentation. (#131)

### Other

* Enable and apply pre-commit with isort/flake8/black. (#116, #125)
* Adjust workflows to only target `main` after merging the `cep-devel` branch. (#141)
* Move `cwp.py` from the repository root to `menuinst._legacy` subpackage.
  It's still shipped to `%PREFIX%` in the conda package. (#145)

### Contributors

* @aganders3
* @dbast
* @jaimergp

### New Contributors

* @dbast made their first contribution in https://github.com/conda/menuinst/pull/116
* @aganders3 made their first contribution in https://github.com/conda/menuinst/pull/119

## 2.0.0 (2023-09-14)

### Enhancements

* Add support for file extension and URL protocol association on Windows. (#117)
* Add support for URL protocol and file type association in all operating systems. Adds tests and examples. (#118 via #119, #135)
* Add `app_user_model_id` field on Windows shortcuts to group taskbar icons together. (#127 via #133)
* Enable automatic elevation on Unix platforms too, and add tests. (#137 via #138, #139)
* Add recipe and CI workflow steps to build and upload canaries to `conda-canary`. (#144, #145, #149)
* Implement auto-elevation logic in Unix systems so it doesn't depend on pre-existing `.nonadmin` files. (#150 via #156)

### Bug fixes

* Ensure some v1-only import paths are still available for backwards compatibility. (#151)
* Do not capitalize `${DISTRIBUTION_NAME}` in v1-style `menuinst` JSON documents. (#153)

### Docs

* Create Sphinx-based documentation following community practices (constructor, conda-libmamba-solver). Absorbs and updates the existing info in wiki and non-deployed docs. (#112)
* Add development documentation. (#131)

### Other

* Enable and apply pre-commit with isort/flake8/black. (#116, #125)
* Adjust workflows to only target `main` after merging the `cep-devel` branch. (#141)
* Move `cwp.py` from the repository root to `menuinst._legacy` subpackage.
  It's still shipped to `%PREFIX%` in the conda package. (#145)


## 1.4.19 (2022-08-17)

  * Remove pywin32 dependency (#103)

## 1.4.18 (2021-09-10)

  * Merge in various patches used by conda-standalone (#85)

    - Do not assume menuinst wants to operate on `sys.prefix`
    - Do not use `runAsAdmin` when the user is not an admin
    - Allow menuinst to operate on non-base prefix
    - Update various tests

## 1.4.17 (2021-07-14)

  * Use distribution name as part of the Start Menu item (#77)
  * Transfer repository to `conda` GitHub organization (#81)
  * Switch from AppVeyor to GitHub Actions for CI (#78, #82, #83)

## 1.4.16 (2019-03-13)

  * Command line option starting with minux, or a space shall not be quoted

## 1.4.15 (2019-03-13)

  * tagged in gonzalo_refactor branch

## 1.4.14 (2018-05-29)

  * clean up and restructure elevation logic
  * unquote HOMEPATH env var as default target location

## 1.4.13 (2018-05-23)

  * Change HOME to HOMEPATH for default shortcut start path

## 1.4.12 (2018-05-10)

  * set default workdir to %HOME% so that it is dynamic per-user
  * fix recursion infinite loop with background processes that had insufficient permissions

## 1.4.11 (2018-02-06)

  * fix #60 more cmd.exe-specific hacking (#61)
  * fix #54 incorrect locale handling (#62)
  * fix logging traceback from #54 (#63)


## 1.4.10 (2017-10-17)

  * better fix for shortcut handling and tidy-ups


## 1.4.9 (2017-10-17)

  * fix cmd.exe / %ComSpec% system shortcut quoting


## 1.4.8 (2017-09-16)

  * fix non-root pythons being used to call cwp.py  #47


## 1.4.7 (2017-05-19)

  * Fixes for Python 2 Unicode conversion in win32.py


## 1.4.6 (2017-05-17)

  * Fix cwp.py after changes to menuinst.knownfolders


## 1.4.5 (2017-05-13)

  * Also use OutputDebugStringW for logging for pythonw.exe


## 1.4.4 (2017-01-23)

  * Set CONDA_PREFIX environment variable in cwp.py, fix PATH


## 1.4.3 (2017-01-19)

  * fix fallback to user-mode shortcut if elevation denied, #39


## 1.4.1 (2016-05-26)

  * Disable 'quicklaunch' shortcuts for SYSTEM user (#33)


## 1.4.0 (2016-05-25)

  * Add license explicitly (BSD 3-clause) (#26)
  * Rework elevation on Windows to not use separate batch file (#27)
  * Improve support for non-ascii characters (#27)
  * Migrate to Windows KnownFolder instead of CSIDL for win > XP (#27)
  * support istalling as SYSTEM user on Windows (for SCCM usage) (#29)
  * Add Appveyor for build testing (#30)
  * Drop CSIDL support in favor of uniform KnownFolder usage (#31)


## 1.3.2 (2016-01-11)

  * keep temporary directory around, due to strange Windows race condition


## 1.3.1 (2015-12-03)

  * add Windows elevation, see PR #22


## 1.3.0 (2015-12-02)

  * add menuinst entry point module menuinst.main
  * fixes for Windows XP


## 1.1.2 (2015-10-27)

  * remove all use of root_prefix (it is always sys.prefix), and subprocess
    calls to Python (which does not work on Windows XP with pythonw.exe)


## 1.1.0 (2015-10-15)

  * add suffix for environment name to shortcuts on win, #4
  * clarify root prefix / env prefix distinction (affects menu names)


## 1.0.4 (2014-07-30)

  * support 'script' key to shortcut to arbitrary executable


## 1.0.3 (2013-10-28)

  * make it compatible with python 3


## 1.0.2 (2013-10-16)

  * add initial support for recognition of non-admin installations
  * make the shortcut function unicode


## 1.0.1 (2013-06-19)

  * fix minor bug on Windows
  * install system wide on Windows


## 1.0.0 (2013-02-25)

  * simplified and changed API
  * removed egginst dependency
  * renamed appinst to menuinst
  * only supports Windows for now


## historical AppInst changelog


### 2012-06-12: 2.1.2

  * use explorer for filebrowser on Windows (PR 2)

  * fixed shortcuts have wrong executable (PR 3)



### 2012-04-25: 2.1.1

  * added ability to specify a working directory via a 'working_dir' key
 …  in a shortcut definition.  This is then used on win32 only to set
    the 'Start in' directory of the created shortcut.

  * On windows the target length is limited to about 260 chars and we use
    python -m webbrowser instead of running the full path to the module to
    reduce the length of the target.



### 2011-03-14: 2.1.0

  * added menu and shortcut removal ability on MaxOSX and Linux

  * removed registry path stuff on Windows, and hence pywin32 dependency

  * add ability to have a menu icon on Linux <custom_tools>/menu.ico

  * removed separate rh3 and rh4 modules

  * simplified much of the code



### 2010-12-09: 2.0.4

  * This version has been used for a long time.


10 October, 2008 (DP):
    - API: Finished refactoring that created the application_menus.py module
        which allows data-driven creation of application menus for both KDE
        and Gnome on RH3, RH4, and probably other modern Linux distributions.
        The RH4 implementation creates application menu files that conform to
        FreeDesktop.org's Desktop Menu Specification 1.0.  Though users may
        need to modify the application_menus.py module to get it to try that
        implementation on another distribution or version.
