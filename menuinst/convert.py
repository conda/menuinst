"""
Converts v1-style menuinst Windows shortcuts to v2 format
"""

import argparse
import json
import sys
from pathlib import Path

VARS_MAPPING = {
    "${PREFIX}": "{{ PREFIX }}",
    "${ROOT_PREFIX}": "{{ BASE_PREFIX }}",
    "${PYTHON_SCRIPTS}": "{{ SCRIPTS_DIR }}",
    "${MENU_DIR}": "{{ MENU_DIR }}",
    "${PERSONALDIR}": "%USERPROFILE%",
    "${USERPROFILE}": "%USERPROFILE%",
    "${ENV_NAME}": "{{ ENV_NAME }}",
    "${DISTRIBUTION_NAME}": "{{ DISTRIBUTION_NAME }}",
    "${PY_VER}": "{{ PY_VER }}",
    "${PLATFORM}": "(64-bit)",
}


def cli() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Converts v1-style menuinst Windows shortcuts to v2 format"
    )
    p.add_argument("path", help="Input v1-style menuinst Windows shortcut")
    p.add_argument("--output", help="Output path for the converted v2 shortcut")
    return p.parse_args()


def _convert_variables(value: str) -> str:
    for old, new in VARS_MAPPING.items():
        value = value.replace(old, new)
    return value


def _convert_common(item):
    return {
        "name": _convert_variables(item["name"]),
        "icon": _convert_variables(item.get("icon", "")).replace("/", "\\") or None,
        "command": [],
        "activate": True,
        "platforms": {
            "win": {
                "desktop": item.get("desktop", True),
                "quicklaunch": item.get("desktop", False),
                "working_dir": (
                    _convert_variables(item.get("workdir", "")).replace("/", "\\") or None
                ),
            },
        },
    }


def _convert_script(item):
    v2 = _convert_common(item)
    v2["platforms"]["win"]["command"] = [
        _convert_variables(item["script"]).replace("/", "\\"),
        *[_convert_variables(arg) for arg in item.get("scriptarguments", ())],
    ]
    return v2


def _convert_pywscript(item):
    v2 = _convert_common(item)
    v2["platforms"]["win"]["command"] = ["{{ PYTHONW }}", _convert_variables(item["pywscript"])]
    return v2


def _convert_pyscript(item):
    v2 = _convert_common(item)
    v2["platforms"]["win"]["command"] = ["{{ PYTHON }}", _convert_variables(item["pyscript"])]
    return v2


def _convert_webbrowser(item):
    v2 = _convert_common(item)
    v2["activate"] = False
    v2["platforms"]["win"]["command"] = [
        "{{ PYTHON }}",
        "-m",
        "webbrowser",
        "-t",
        item["webbrowser"],
    ]
    return v2


def _convert_system(item):
    v2 = _convert_common(item)
    v2["activate"] = False
    v2["platforms"]["win"]["command"] = [
        _convert_variables(item["system"]),
        *[_convert_variables(arg) for arg in item.get("scriptarguments", ())],
    ]
    return v2


def convert(path):
    v1 = json.loads(Path(path).read_text())
    if "$schema" in v1:
        raise ValueError(f"Input '{path}' seems to be a menuinst v2 shortcut already.")
    v2 = {
        "$schema": (
            "https://raw.githubusercontent.com/conda/menuinst"
            "/refs/heads/main/menuinst/data/menuinst.schema.json"
        ),
        "menu_name": _convert_variables(v1["menu_name"]),
    }
    items = []
    for v1_item in v1["menu_items"]:
        if "script" in v1_item:
            items.append(_convert_script(v1_item))
        elif "pywscript" in v1_item:
            items.append(_convert_pywscript(v1_item))
        elif "pyscript" in v1_item:
            items.append(_convert_pyscript(v1_item))
        elif "webbrowser" in v1_item:
            items.append(_convert_webbrowser(v1_item))
        elif "system" in v1_item:
            items.append(_convert_system(v1_item))
        else:
            raise ValueError(f"Unrecognized item:\n{v1_item}")
    v2["menu_items"] = items
    return v2


def write(data, output) -> Path:
    output = Path(output)
    if output.exists():
        raise RuntimeError(f"Output '{output}' exists. Please choose a different one.")
    output.write_text(json.dumps(data, indent=2))
    return output


def main():
    args = cli()
    v2 = convert(args.path)
    if args.output:
        write(v2, args.output)
    else:
        print(json.dumps(v2, indent=2))


if __name__ == "__main__":
    sys.exit(main())
