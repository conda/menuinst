"""Ensure JSON schemas are up-to-date with code"""

import json

import pytest

from menuinst._schema import SCHEMA_VERSION, dump_default_to_json, dump_schema_to_json
from menuinst.platforms.base import SCHEMA_VERSION as SCHEMA_VERSION_BASE
from menuinst.utils import data_path


def test_schema_is_up_to_date():
    with open(data_path(f"menuinst-{SCHEMA_VERSION}.schema.json")) as f:
        in_file = json.load(f)
    in_code = dump_schema_to_json(write=False)
    assert in_file == in_code


def test_defaults_are_up_to_date():
    with open(data_path(f"menuinst-{SCHEMA_VERSION}.default.json")) as f:
        in_file = json.load(f)
    in_code = dump_default_to_json(write=False)
    assert in_file == in_code


def test_schema_versions_in_sync():
    assert SCHEMA_VERSION_BASE == SCHEMA_VERSION, (
        "meninst._schema and menuinst.platforms.base must have the same 'SCHEMA_VERSION' value"
    )


@pytest.mark.parametrize("datatype", ("default", "schema"))
def test_links_point_to_latest_version(datatype: str):
    latest_file = data_path(f"menuinst-{SCHEMA_VERSION}.{datatype}.json")
    symlink = data_path(f"menuinst.{datatype}.json")
    assert latest_file.exists()
    assert symlink.exists()
    if symlink.is_symlink():
        assert symlink.samefile(latest_file)
    else:
        # GitHub runners do not support symlinks
        assert symlink.read_text() == latest_file.name
