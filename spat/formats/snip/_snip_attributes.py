from enum import Enum, unique
from typing import Literal, Union

from pydantic import Field

from ...model import Model


@unique
class SnipAttributeType(str, Enum):
    """Snip attributes can have these fundamental types."""

    INT = "int"
    STR = "str"
    ENUM = "enum"


########################################################################################
### Attribute declarations
########################################################################################
class SnipIntDeclaration(Model):
    """Type declaration of an integer snip attribute."""

    type_: Literal[SnipAttributeType.INT] = Field(alias="type")


class SnipStrDeclaration(Model):
    """Type declaration of a string snip attribute."""

    type_: Literal[SnipAttributeType.STR] = Field(alias="type")


class SnipEnumDeclaration(Model):
    """Type declaration of an enum snip attribute."""

    type_: Literal[SnipAttributeType.ENUM] = Field(alias="type")
    values: frozenset[str]


########################################################################################
### Attribute instances
########################################################################################
class SnipInt(Model):
    """Instance of an integer snip attribute."""

    type_: Literal[SnipAttributeType.INT] = Field(alias="type")
    value: int


class SnipStr(Model):
    """Instance of a string snip attribute."""

    type_: Literal[SnipAttributeType.STR] = Field(alias="type")
    value: str


class SnipEnum(Model):
    """Instance of an enum snip attribute."""

    type_: Literal[SnipAttributeType.ENUM] = Field(alias="type")
    value: str


# We use the `type_` field to disambiguate how pydantic parses the `Union`s.
# See https://github.com/samuelcolvin/pydantic/issues/619
SnipAttributeDeclaration = Union[
    SnipIntDeclaration, SnipStrDeclaration, SnipEnumDeclaration
]
SnipAttribute = Union[SnipInt, SnipStr, SnipEnum]
