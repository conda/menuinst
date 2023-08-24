"""
"""

import os
from logging import basicConfig as _basicConfig

import apipkg as _apipkg

try:
    from ._version import __version__
except ImportError:
    __version__ = "dev"

from .api import _install_adapter as install  # noqa

if os.environ.get("MENUINST_DEBUG"):
    _basicConfig(level="DEBUG")

# Compatibility forwarders for menuinst v1.x (Windows only)
if os.name == "nt":
    # Calling initpkg clears the 'menuinst' top-level namespace and replaces it with exportdefs
    # if we want to keep something defined here, use the attr dictionary
    _apipkg.initpkg(
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
        attr={"__version__": __version__, "install": install},
    )
