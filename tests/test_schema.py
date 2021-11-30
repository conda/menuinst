from pprint import pprint

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis_jsonschema import from_schema
from pydantic import ValidationError

from menuinst.schema import MenuInstSchema, validate
from conftest import DATA

# # suppress_health_check=3 --> too_slow
# @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
# @given(from_schema(MenuInstSchema.schema()))
# def test_schema_can_be_loaded(value):
#     assert value


@pytest.mark.parametrize("path", (DATA / "jsons").glob("*.json"))
def test_examples(path):
    if "invalid" in path.name:
        with pytest.raises(ValidationError):
            assert validate(path)
    else:
        assert validate(path)
