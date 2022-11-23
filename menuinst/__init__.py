"""
"""

import os
import sys
import json
from logging import getLogger as _getLogger

try:
    from ._version import __version__
except ImportError:
    __version__ = "dev"


from ._legacy import install as _legacy_install
from .api import install as _api_install, remove as _api_remove
from .utils import DEFAULT_PREFIX, DEFAULT_BASE_PREFIX

_log = _getLogger(__name__)


def install(path, remove=False, prefix=DEFAULT_PREFIX, **kwargs):
    """
    This function is only here as a legacy adapter.
    Please use menuinst.api functions instead.
    """
    if sys.platform == "win32":
        path = path.replace("/", "\\")
    json_path = os.path.join(prefix, path)
    with open(json_path) as f:
        metadata = json.load(f)
    if "$id" not in metadata:  # old style JSON
        if sys.platform == "win32":
            kwargs.setdefault("root_prefix", kwargs.pop("base_prefix", DEFAULT_BASE_PREFIX))
            _legacy_install(json_path, remove=remove, prefix=prefix, **kwargs)
        else:
            _log.warn(
                "menuinst._legacy is only supported on Windows. "
                "Switch to the new-style menu definitions "
                "for cross-platform compatibility."
            )
    else:
        # patch kwargs to reroute root_prefix to base_prefix
        kwargs.setdefault("base_prefix", kwargs.pop("root_prefix", DEFAULT_BASE_PREFIX))
        if remove:
            _api_remove(metadata, target_prefix=prefix, **kwargs)
        else:
            _api_install(metadata, target_prefix=prefix, **kwargs)
