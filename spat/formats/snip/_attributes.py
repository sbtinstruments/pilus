from .._parser_map import register_parser
from ..model import Model


class AttributeEnum(Model):
    values: frozenset[str]


class AttributeTypes(Model):
    # TODO: Replace `dict` with `immutables.Map` when pydantic supports custom
    # data types.
    enums: dict[str, AttributeEnum]


class Attributes(Model):
    """Attributes for the snip format."""

    types: AttributeTypes


register_parser("application/vnd.sbt.snip.attributes+json", Attributes.from_json_data)
