from __future__ import annotations

from enum import Enum, unique
from typing import Any, ClassVar, Literal, Type, TypeVar, Union

from pydantic import Field, validator

from ..model import FrozenModel


@unique
class _SnipAttrType(str, Enum):
    """Snip attributes can have these fundamental types."""

    INT = "int"
    STR = "str"
    ENUM = "enum"


########################################################################################
### Attribute declarations
###
### Note that the `type_` field is there to force pydantic to parse correctly (see [1]).
########################################################################################
T = TypeVar("T", bound="SnipDeclBase")


class SnipDeclBase(FrozenModel):
    """Base class for all snip attribute declarations."""

    declaration_type: ClassVar[_SnipAttrType]

    @classmethod
    def from_args(cls: Type[T], **kwargs: Any) -> T:
        """Return instance with the `type_` field filled out for convenience."""
        return cls(type=cls.declaration_type, **kwargs)


class SnipIntDecl(SnipDeclBase):
    """Type declaration of an integer snip attribute."""

    declaration_type: ClassVar[_SnipAttrType] = _SnipAttrType.INT
    type_: Literal[_SnipAttrType.INT] = Field(alias="type")


class SnipStrDecl(SnipDeclBase):
    """Type declaration of a string snip attribute."""

    declaration_type: ClassVar[_SnipAttrType] = _SnipAttrType.STR
    type_: Literal[_SnipAttrType.STR] = Field(alias="type")


class SnipEnumDecl(SnipDeclBase):
    """Type declaration of an enum snip attribute."""

    declaration_type: ClassVar[_SnipAttrType] = _SnipAttrType.ENUM
    type_: Literal[_SnipAttrType.ENUM] = Field(alias="type")
    values: frozenset[str]


########################################################################################
### Attribute instances
########################################################################################
class SnipInt(FrozenModel):
    """Instance of an integer snip attribute."""

    declaration: SnipIntDecl
    value: int


class SnipStr(FrozenModel):
    """Instance of a string snip attribute."""

    declaration: SnipStrDecl
    value: str


class SnipEnum(FrozenModel):
    """Instance of an enum snip attribute."""

    declaration: SnipEnumDecl
    value: str

    @validator("value")
    def value_must_be_in_enum(  # pylint: disable=no-self-use,no-self-argument
        cls, v: str, values: Any
    ) -> str:
        """Ensure that the value is part of the enum."""
        declaration: SnipEnumDecl = values["declaration"]
        if v not in declaration.values:
            raise ValueError(
                f'Value "{v}" is not part of the enum {declaration.values}'
            )
        return v


# [1] We use the `type_` field to disambiguate how pydantic parses the `Union`s.
# See https://github.com/samuelcolvin/pydantic/issues/619
SnipAttrDecl = Union[SnipIntDecl, SnipStrDecl, SnipEnumDecl]
SnipAttr = Union[SnipInt, SnipStr, SnipEnum]
