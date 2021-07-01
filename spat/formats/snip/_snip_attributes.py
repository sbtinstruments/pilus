from __future__ import annotations

from enum import Enum, unique
from typing import Any, ClassVar, Literal, Type, TypeVar, Union

from pydantic import Field, validator

from ...model import Model


@unique
class _SnipAttributeType(str, Enum):
    """Snip attributes can have these fundamental types."""

    INT = "int"
    STR = "str"
    ENUM = "enum"


########################################################################################
### Attribute declarations
###
### Note that the `type_` field is there to force pydantic to parse correctly (see [1]).
########################################################################################
T = TypeVar("T", bound="SnipDeclarationBase")


class SnipDeclarationBase(Model):
    """Base class for all snip attribute declarations."""

    declaration_type: ClassVar[_SnipAttributeType]

    @classmethod
    def from_args(cls: Type[T], **kwargs: Any) -> T:
        """Return instance with the `type_` field filled out for convenience."""
        return cls(type=cls.declaration_type, **kwargs)


class SnipIntDeclaration(SnipDeclarationBase):
    """Type declaration of an integer snip attribute."""

    declaration_type: ClassVar[_SnipAttributeType] = _SnipAttributeType.INT
    type_: Literal[_SnipAttributeType.INT] = Field(alias="type")


class SnipStrDeclaration(SnipDeclarationBase):
    """Type declaration of a string snip attribute."""

    declaration_type: ClassVar[_SnipAttributeType] = _SnipAttributeType.STR
    type_: Literal[_SnipAttributeType.STR] = Field(alias="type")


class SnipEnumDeclaration(SnipDeclarationBase):
    """Type declaration of an enum snip attribute."""

    declaration_type: ClassVar[_SnipAttributeType] = _SnipAttributeType.ENUM
    type_: Literal[_SnipAttributeType.ENUM] = Field(alias="type")
    values: frozenset[str]


########################################################################################
### Attribute instances
########################################################################################
class SnipInt(Model):
    """Instance of an integer snip attribute."""

    declaration: SnipIntDeclaration
    value: int


class SnipStr(Model):
    """Instance of a string snip attribute."""

    declaration: SnipStrDeclaration
    value: str


class SnipEnum(Model):
    """Instance of an enum snip attribute."""

    declaration: SnipEnumDeclaration
    value: str

    @validator("value")
    def value_must_be_in_enum(  # pylint: disable=no-self-use,no-self-argument
        cls, v: str, values: Any
    ) -> str:
        """Ensure that the value is part of the enum."""
        declaration: SnipEnumDeclaration = values["declaration"]
        if v not in declaration.values:
            raise ValueError(
                f'Value "{v}" is not part of the enum {declaration.values}'
            )
        return v


# [1] We use the `type_` field to disambiguate how pydantic parses the `Union`s.
# See https://github.com/samuelcolvin/pydantic/issues/619
SnipAttributeDeclaration = Union[
    SnipIntDeclaration, SnipStrDeclaration, SnipEnumDeclaration
]
SnipAttribute = Union[SnipInt, SnipStr, SnipEnum]
