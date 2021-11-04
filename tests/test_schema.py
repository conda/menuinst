from pprint import pprint

import pytest
from hypothesis import given, settings
from hypothesis_jsonschema import from_schema

from menuinst.schema import MenuInstSchema, validate
from conftest import DATA


@settings(max_examples=100)
@given(from_schema(MenuInstSchema.schema()))
def test_property(value):
    pprint(value)


@pytest.mark.parametrize("path", DATA.glob("*.json"))
def test_examples(path):
    assert validate(path)
