"""
"""

import json
import os
import sys
from logging import basicConfig, getLogger

from .utils import DEFAULT_BASE_PREFIX, DEFAULT_PREFIX

try:
    from ._version import __version__
except ImportError:
    __version__ = "dev"

log = getLogger(__name__)
if os.environ.get("MENUINST_DEBUG"):
    basicConfig(level="DEBUG")

__all__ = ["install", "__version__"]


def install(
    path: os.PathLike, remove: bool = False, prefix: os.PathLike = DEFAULT_PREFIX, **kwargs
):
    """
    This function is only here as a legacy adapter for menuinst v1.x.
    Please use `menuinst.api` functions instead.
    """
    if sys.platform == "win32":
        path = path.replace("/", "\\")
    json_path = os.path.join(prefix, path)
    with open(json_path) as f:
        metadata = json.load(f)
    if "$id" not in metadata:  # old style JSON
        from ._legacy import install as _legacy_install

        if sys.platform == "win32":
            kwargs.setdefault("root_prefix", kwargs.pop("base_prefix", DEFAULT_BASE_PREFIX))
            if kwargs["root_prefix"] is None:
                kwargs["root_prefix"] = DEFAULT_BASE_PREFIX
            _legacy_install(json_path, remove=remove, prefix=prefix, **kwargs)
        else:
            log.warn(
                "menuinst._legacy is only supported on Windows. "
                "Switch to the new-style menu definitions "
                "for cross-platform compatibility."
            )
    else:
        from .api import install as _api_install
        from .api import remove as _api_remove

        # patch kwargs to reroute root_prefix to base_prefix
        kwargs.setdefault("base_prefix", kwargs.pop("root_prefix", DEFAULT_BASE_PREFIX))
        if kwargs["base_prefix"] is None:
            kwargs["base_prefix"] = DEFAULT_BASE_PREFIX
        if remove:
            _api_remove(metadata, target_prefix=prefix, **kwargs)
        else:
            _api_install(metadata, target_prefix=prefix, **kwargs)


# Compatibility forwarders for menuinst v1.x (Windows only)
if os.name == "nt":
    import apipkg

    apipkg.initpkg(
        __name__,
        exportdefs={
            "win32": {
                "dirs_src": "menuinst.platforms.win_utils.knownfolders:dirs_src",
            },
            "knownfolders": {
                "get_folder_path": "menuinst.platforms.win_utils.knownfolders:get_folder_path",
                "FOLDERID": "menuinst.platforms.win_utils.knownfolders:FOLDERID",
            },
            "winshortcut": {
                "create_shortcut": "menuinst.platforms.win_utils.winshortcut:create_shortcut",
            },
            "win_elevate": {
                "runAsAdmin": "menuinst.platforms.win_utils.win_elevate:runAsAdmin",
                "isUserAdmin": "menuinst.platforms.win_utils.win_elevate:isUserAdmin",
            },
        },
        # Calling initpkg clears the 'menuinst' top-level namespace and replaces it with exportdefs
        # if we want to keep something defined in this module, use the attr dictionary
        attr={"__version__": __version__, "install": install},
    )
