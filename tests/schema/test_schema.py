from hypothesis import given, settings
from hypothesis_jsonschema import from_schema
from menuinst.schema.generate_schema import MenuInstSchema
from pprint import pprint


@settings(max_examples=100)
@given(from_schema(MenuInstSchema.schema()))
def test_property(value):
    pprint(value)
