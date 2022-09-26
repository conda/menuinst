from functools import wraps
from pathlib import Path
import logging
import os
import sys


def elevate_as_needed(func):
    if sys.platform != "win32":
        return func

    @wraps(func)
    def wrapper_elevate(
        *args,
        base_prefix: os.PathLike = sys.prefix,
        **kwargs,
    ):
        from .win_elevate import isUserAdmin, runAsAdmin

        kwargs.pop("_mode", None)
        fallback_to_user_mode = True
        if not (Path(base_prefix) / ".nonadmin").exists():
            if isUserAdmin():
                return func(
                    base_prefix=base_prefix,
                    _mode="system",
                    *args,
                    **kwargs,
                )
            if os.environ.get("_MENUINST_RECURSING") != "1":
                # call the wrapped func with elevated prompt...
                # from the command line; not pretty!
                try:
                    return_code = runAsAdmin(
                        [
                            Path(base_prefix) / "python",
                            "-c",
                            f"import os;"
                            f"os.environ.setdefault('_MENUINST_RECURSING', '1');"
                            f"from {func.__module__} import {func.__name__};"
                            f"{func.__name__}("
                            f"*{args!r},"
                            f"base_prefix={base_prefix!r},"
                            f"**{kwargs!r}"
                            ")",
                        ]
                    )
                    if not return_code:  # success, no need to fallback
                        fallback_to_user_mode = False
                    os.environ.pop("_MENUINST_RECURSING", None)
                except OSError:
                    logging.warn(
                        "Could not write menu folder! Insufficient permissions? "
                        "Falling back to user location"
                    )
        if fallback_to_user_mode:
            return func(
                base_prefix=base_prefix,
                _mode="user",
                *args,
                **kwargs,
            )

    return wrapper_elevate
