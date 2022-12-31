import pytest

# from hypothesis import given, settings, HealthCheck
# from hypothesis_jsonschema import from_schema
from pydantic import ValidationError

from menuinst._schema import validate, MenuItemMetadata, OptionalMenuItemMetadata
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

def test_MenuItemMetadata_synced_with_OptionalMenuItemMetadata():
    fields_as_required = MenuItemMetadata.__fields__
    fields_as_optional = OptionalMenuItemMetadata.__fields__
    assert fields_as_required.keys() == fields_as_optional.keys()
    for required, optional in zip(fields_as_required.values(), fields_as_optional.values()):
        assert required.field_info.description == optional.field_info.description
