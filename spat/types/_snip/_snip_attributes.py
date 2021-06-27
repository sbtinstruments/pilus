from enum import Enum, unique
from typing import Literal, Union

from pydantic import Field

from ...model import Model


@unique
class SnipAttributeType(str, Enum):
    INT = "int"
    STR = "str"
    ENUM = "enum"


########################################################################################
### Attribute declarations
########################################################################################
class SnipIntDeclaration(Model):
    type_: Literal[SnipAttributeType.INT] = Field(alias="type")


class SnipStrDeclaration(Model):
    type_: Literal[SnipAttributeType.STR] = Field(alias="type")


class SnipEnumDeclaration(Model):
    type_: Literal[SnipAttributeType.ENUM] = Field(alias="type")
    values: frozenset[str]


########################################################################################
### Attribute instances
########################################################################################
class SnipInt(Model):
    type_: Literal[SnipAttributeType.INT] = Field(alias="type")
    value: int


class SnipStr(Model):
    type_: Literal[SnipAttributeType.STR] = Field(alias="type")
    value: str


class SnipEnum(Model):
    type_: Literal[SnipAttributeType.ENUM] = Field(alias="type")
    value: str


# We use the `type_` field to disambiguate how pydantic parses the `Union`s.
# See https://github.com/samuelcolvin/pydantic/issues/619
SnipAttributeDeclaration = Union[
    SnipIntDeclaration, SnipStrDeclaration, SnipEnumDeclaration
]
SnipAttribute = Union[SnipInt, SnipStr, SnipEnum]
