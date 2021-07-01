from __future__ import annotations

from typing import Iterable, Optional

from pydantic import validator

from ...model import Model, add_media_type
from ._snip_attributes import (
    SnipAttribute,
    SnipAttributeDeclaration,
    SnipEnum,
    SnipEnumDeclaration,
    SnipInt,
    SnipIntDeclaration,
    SnipStr,
    SnipStrDeclaration,
)

# TODO: Replace `dict` with `immutables.Map` when pydantic supports custom
# data types.
_RootType = dict[str, SnipAttributeDeclaration]


@add_media_type("application/vnd.sbt.snip.attributes+json")
class SnipAttributeDeclarationMap(Model):
    """Attribute declarations for snip."""

    __root__: _RootType

    @property
    def enums(self) -> Iterable[tuple[str, SnipEnumDeclaration]]:
        """Return all (name, enum) pairs."""
        return _get_enums(self.__root__)

    def parse_kwargs(self, **kwargs: str) -> Iterable[tuple[str, SnipAttribute]]:
        """Return all (name, attribute) pairs based on the kwargs."""
        for name, value in kwargs.items():
            # Find type
            try:
                declaration = self.__root__[name]
            except KeyError as exc:
                raise ValueError(f'There is no attribute named "{name}"') from exc
            # Int
            if isinstance(declaration, SnipIntDeclaration):
                if not isinstance(value, int):
                    raise ValueError(f'The value "{value}" is not an integer')
                yield (name, SnipInt(declaration=declaration, value=value))
            # Str
            elif isinstance(declaration, SnipStrDeclaration):
                if not isinstance(value, str):
                    raise ValueError(f'The value "{value}" is not a string')
                yield (name, SnipStr(declaration=declaration, value=value))
            # Enum
            elif isinstance(declaration, SnipEnumDeclaration):
                if value not in declaration.values:
                    raise ValueError(
                        f'There is no value named "{value}" in the "{name}" enum'
                    )
                yield (name, SnipEnum(declaration=declaration, value=value))

    def parse_raw_attributes(
        self, raw_attributes: Iterable[str]
    ) -> Iterable[tuple[str, SnipAttribute]]:
        """Return all (name, attribute) pairs based on the raw string attributes."""
        return (self.parse_raw_attribute(s) for s in raw_attributes)

    def parse_raw_attribute(self, raw_attribute: str) -> tuple[str, SnipAttribute]:
        """Return a (name, attribute) pair based on the raw string attribute."""
        parts = raw_attribute.split("=")
        len_parts = len(parts)
        # If there is no attribute name, we assume that the attribute is an enum.
        # This is why we require that enum values are globally unique at [1].
        if len_parts == 1:
            value = raw_attribute
            result = self.get_enum_from_value(value)
            if result is None:
                raise ValueError(f'Could not find enum value "{value}"')
            return result
        # We got both a name and a value
        if len_parts == 2:
            name, raw_value = parts
            # Find type
            try:
                declaration = self.__root__[name]
            except KeyError as exc:
                raise ValueError(f'There is no attribute named "{name}"') from exc
            # Int
            if isinstance(declaration, SnipIntDeclaration):
                return (name, SnipInt(declaration=declaration, value=int(raw_value)))
            # Str
            if isinstance(declaration, SnipStrDeclaration):
                return (name, SnipStr(declaration=declaration, value=raw_value))
            # Enum
            if isinstance(declaration, SnipEnumDeclaration):
                if raw_value not in declaration.values:
                    raise ValueError(
                        f'There is no value named "{raw_value}" in the "{name}" enum'
                    )
                return (name, SnipEnum(declaration=declaration, value=raw_value))
        raise ValueError(f'Could not parse attribute: "{raw_attribute}"')

    def get_enum_from_value(self, value: str) -> Optional[tuple[str, SnipEnum]]:
        """Return the (name, enum) pair that corresponds to the given value."""
        for name, enum in self.enums:
            if value in enum.values:
                return name, SnipEnum(declaration=enum, value=value)
        return None

    @validator("__root__")
    def enum_values_are_globally_unique(  # pylint: disable=no-self-argument,no-self-use
        cls, v: _RootType
    ) -> _RootType:  # [1]
        """Ensure that there are no enum value conflicts."""
        values = tuple(_get_enum_values(v))
        if len(values) != len(frozenset(values)):
            raise ValueError("Enum values are not globally unique")
        return v


def _get_enum_values(types: _RootType) -> Iterable[str]:
    for _, enum in _get_enums(types):
        yield from enum.values


def _get_enums(types: _RootType) -> Iterable[tuple[str, SnipEnumDeclaration]]:
    return (
        (name, t) for name, t in types.items() if isinstance(t, SnipEnumDeclaration)
    )
