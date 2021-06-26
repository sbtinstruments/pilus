from dataclasses import dataclass
from typing import Iterable, Union

from pydantic import validator

from ...formats import register_parser
from ...formats.model import Model


class SnipEnum(Model):
    value: str


SnipAttribute = Union[SnipEnum]

SnipAttributeSet = frozenset[SnipAttribute]


class SnipEnumType(Model):
    values: frozenset[str]


class SnipTypeDeclaration(Model):
    # TODO: Replace `dict` with `immutables.Map` when pydantic supports custom
    # data types.
    enums: dict[str, SnipEnumType]

    def enum_values(self) -> Iterable[str]:
        return _get_values(self.enums.values())

    @validator("enums")
    def enums_are_globally_unique(
        cls, v: dict[str, SnipEnumType]
    ) -> dict[str, SnipEnumType]:
        values = tuple(_get_values(v.values()))
        if len(values) != len(frozenset(values)):
            raise ValueError("Enum values must be globally unique")
        return v


def _get_values(enums: Iterable[SnipEnumType]) -> Iterable[str]:
    for enum in enums:
        yield from enum.values


class SnipAttributeDeclaration(Model):
    """Attribute declaration for snip."""

    types: SnipTypeDeclaration

    def parse_strings(self, raw_attributes: Iterable[str]) -> Iterable[SnipAttribute]:
        return (self.parse_string(s) for s in raw_attributes)

    def parse_string(self, raw_attribute: str) -> SnipAttribute:
        if raw_attribute in self.types.enum_values():
            return SnipEnum(value=raw_attribute)
        raise ValueError(f'Could not parse attribute: "{raw_attribute}"')


register_parser(
    "application/vnd.sbt.snip.attributes+json", SnipAttributeDeclaration.from_json_data
)
