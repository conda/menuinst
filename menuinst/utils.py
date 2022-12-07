import logging
import os
import re
import shlex
import subprocess
import sys
import traceback
import xml.etree.ElementTree as XMLTree
from contextlib import suppress
from functools import wraps
from pathlib import Path
from unicodedata import normalize
from typing import Union, Literal


def _default_prefix(which: Union[Literal["target"], Literal["base"]] = "target"):
    """
    The prefixes in menuinst need to be handled with care.

    Conda installations that require superuser permissions need elevation for
    the creation of shortcuts. Constructor will leave a sentinel file to signal
    this. If a file `.nonadmin` is present in the 'base' environment (or root of
    the installation directory if conda is not present), superuser access is not
    needed.

    In order to check for this file, menuinst needs to track 'base_prefix'. For
    a regular 'conda' process, this should be `conda.base.context.context.root_prefix'.
    However, constructor also relies on a pyinstaller-frozen conda installation,
    'conda-standalone'. In these cases, 'sys.prefix' is set to temporary location
    of the extracted contents of the executable -- that's NOT the base installation!

    For those reasons, we handle the default prefix with 'sys.prefix' (or 'sys.base_prefix')
    as a last resort. The logic is:

    - If 'MENUINST_PREFIX' (or 'MENUINST_BASE_PREFIX') is an env var with a set value, use that.
    - If are already using conda, we get the context object and use those values.
    - If CONDA_PREFIX (or 'CONDA_ROOT_PREFIX') are available, use those
    - Last resort: use sys.prefix and sys.base_prefix

    This helps us pass a lot of CLI arguments back and forth.
    """
    base = which == "base"
    context = None
    if "conda" in sys.modules:
        with suppress(ImportError):
            from conda.base.context import context

    if base:
        prefix = os.environ.get("MENUINST_BASE_PREFIX")
        if prefix:
            return prefix 
        if context:
            return context.root_prefix
        return os.environ.get("CONDA_ROOT_PREFIX", sys.base_prefix)
    # else
    prefix = os.environ.get("MENUINST_PREFIX")
    if prefix:
        return prefix 
    if context:
        return context.target_prefix
    return os.environ.get("CONDA_PREFIX", sys.prefix)


DEFAULT_PREFIX = _default_prefix("target")
DEFAULT_BASE_PREFIX = _default_prefix("base")


def slugify(text):
    # Adapted from from django.utils.text.slugify
    # Copyright (c) Django Software Foundation and individual contributors.
    # All rights reserved.
    # Redistribution and use in source and binary forms, with or without modification,
    # are permitted provided that the following conditions are met:
    #     1. Redistributions of source code must retain the above copyright notice,
    #     this list of conditions and the following disclaimer.
    #     2. Redistributions in binary form must reproduce the above copyright
    #     notice, this list of conditions and the following disclaimer in the
    #     documentation and/or other materials provided with the distribution.
    #     3. Neither the name of Django nor the names of its contributors may be used
    #     to endorse or promote products derived from this software without
    #     specific prior written permission.
    # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
    # ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    # WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    # DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
    # ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
    # (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
    # LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
    # ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    # (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    # SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
    """
    Convert to ASCII, and spaces to hyphens.
    Remove characters that aren't alphanumerics, underscores, or hyphens.
    Convert to lowercase. Also strip leading and trailing whitespace.
    """
    text = normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)


def indent_xml_tree(elem, level=0):
    """
    adds whitespace to the tree, so that it results in a pretty printed tree
    """
    indentation = "    "  # 4 spaces, just like in Python!
    base_indentation = "\n" + level * indentation
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = base_indentation + indentation
        for e in elem:
            indent_xml_tree(e, level + 1)
            if not e.tail or not e.tail.strip():
                e.tail = base_indentation + indentation
        if not e.tail or not e.tail.strip():
            e.tail = base_indentation
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = base_indentation


def add_xml_child(parent, tag, text=None):
    """
    Add a child element of specified tag type to parent.
    The new child element is returned.
    """
    elem = XMLTree.SubElement(parent, tag)
    if text is not None:
        elem.text = text
    return elem


class WinLex:
    @classmethod
    def quote_args(cls, args):
        # cmd.exe /K or /C expects a single string argument and requires
        # doubled-up quotes when any sub-arguments have spaces:
        # https://stackoverflow.com/a/6378038/3257826
        if (
            len(args) > 2
            and ("CMD.EXE" in args[0].upper() or "%COMSPEC%" in args[0].upper())
            and (args[1].upper() == "/K" or args[1].upper() == "/C")
            and any(" " in arg for arg in args[2:])
        ):
            args = [
                cls.ensure_pad(args[0], '"'),  # cmd.exe
                args[1],  # /K or /C
                '"%s"' % (" ".join(cls.ensure_pad(arg, '"') for arg in args[2:])),  # double-quoted
            ]
        else:
            args = [cls.quote_string(arg) for arg in args]
        return args

    @classmethod
    def quote_string(cls, s):
        """
        quotes a string if necessary.
        """
        # strip any existing quotes
        s = s.strip('"')
        # don't add quotes for minus or leading space
        if s[0] in ("-", " "):
            return s
        if " " in s or "/" in s:
            return '"%s"' % s
        return s

    @classmethod
    def ensure_pad(cls, name, pad="_"):
        """

        Examples:
            >>> ensure_pad('conda')
            '_conda_'

        """
        if not name or name[0] == name[-1] == pad:
            return name
        else:
            return "%s%s%s" % (pad, name, pad)


class UnixLex:
    @classmethod
    def quote_args(cls, args):
        return [cls.quote_string(a) for a in args]

    @classmethod
    def quote_string(cls, s):
        quoted = shlex.quote(s)
        if quoted.startswith("'") and not '"' in quoted:
            quoted = f'"{quoted[1:-1]}"'
        return quoted


def unlink(path, missing_ok=False):
    try:
        os.unlink(path)
    except FileNotFoundError as exc:
        if not missing_ok:
            raise exc


def data_path(path):
    here = Path(__file__).parent
    return here / "data" / path


def deep_update(mapping, *updating_mappings):
    # Brought from pydantic.utils
    # https://github.com/samuelcolvin/pydantic/blob/9d631a3429a66f30742c1a52c94ac18ec6ba848d/pydantic/utils.py#L198

    # The MIT License (MIT)
    # Copyright (c) 2017, 2018, 2019, 2020, 2021 Samuel Colvin and other contributors
    # Permission is hereby granted, free of charge, to any person obtaining a copy
    # of this software and associated documentation files (the "Software"), to deal
    # in the Software without restriction, including without limitation the rights
    # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    # copies of the Software, and to permit persons to whom the Software is
    # furnished to do so, subject to the following conditions:
    # The above copyright notice and this permission notice shall be included in all
    # copies or substantial portions of the Software.
    # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    # SOFTWARE.

    updated_mapping = mapping.copy()
    for updating_mapping in updating_mappings:
        for k, v in updating_mapping.items():
            if k in updated_mapping and isinstance(updated_mapping[k], dict) and isinstance(v, dict):
                updated_mapping[k] = deep_update(updated_mapping[k], v)
            else:
                updated_mapping[k] = v
    return updated_mapping


def user_is_admin():
    if os.name == 'nt':
        from .platforms.win_utils.win_elevate import isUserAdmin 

        return isUserAdmin()
    elif os.name == 'posix':
        # Check for root on Linux, macOS and other posix systems
        return os.getuid() == 0
    else:
        raise RuntimeError(f"Unsupported operating system: {os.name}")


def run_as_admin(argv) -> int:
    """
    Rerun this command in a new process with admin permissions.
    """
    if os.name == 'nt':
        from .platforms.win_utils.win_elevate import runAsAdmin

        return runAsAdmin(argv)
    elif os.name == 'posix':
        return subprocess.call(["sudo", *argv])
    else:
        raise RuntimeError(f"Unsupported operating system: {os.name}")


def elevate_as_needed(func):
    """
    Multiplatform decorator to run a function as a superuser, if needed.

    This depends on the presence of a `.nonadmin` file in the installation root.
    This is usually planted by the `constructor` installer if the installation
    process didn't need superuser permissions.

    In the absence of this file, we assume that we will need superuser
    permissions, so we try to run the decorated function as a superuser.
    If that fails (the user rejects the request or doesn't have permissions
    to accept it), we'll try to run it as a normal user.

    NOTE: Only functions that return None should be decorated. The function
    will run in a separate process, so we won't be able to capture the return
    value anyway.
    """
    if os.name != "nt":
        return func

    @wraps(func)
    def wrapper_elevate(
        *args,
        base_prefix: os.PathLike = None,
        **kwargs,
    ):
        kwargs.pop("_mode", None)
        base_prefix = base_prefix or DEFAULT_BASE_PREFIX
        if not (Path(base_prefix) / ".nonadmin").exists():
            if user_is_admin():
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
                    executable = [sys.executable]
                    if getattr(sys, 'frozen', False):
                        executable.append("python")
                    return_code = run_as_admin(
                        [
                            *executable,
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
                except Exception:
                    logging.warn(
                        "Could not write menu folder! Falling back to user mode.\n%s",
                        "\n".join(traceback.format_exc())
                    )
                else:
                    os.environ.pop("_MENUINST_RECURSING", None)
                    if return_code == 0:  # success, no need to fallback
                        return 
        # We have not returned yet? Well, let's try as a normal user
        return func(
            base_prefix=base_prefix,
            _mode="user",
            *args,
            **kwargs,
        )

    return wrapper_elevate
