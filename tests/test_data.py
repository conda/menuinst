"""Ensure JSON schemas are up-to-date with code"""

import json

import pytest

from menuinst.utils import data_path
from menuinst.schema import dump_default_to_json, dump_schema_to_json


@pytest.mark.pydantic
def test_schema_is_up_to_date():
    with open(data_path("menuinst.schema.json")) as f:
        in_file = json.load(f)
    in_code = dump_schema_to_json(write=False)
    assert in_file == in_code


@pytest.mark.pydantic
def test_defaults_are_up_to_date():
    with open(data_path("menuinst.menu_item.default.json")) as f:
        in_file = json.load(f)
    in_code = dump_default_to_json(write=False)
    assert in_file == in_code
