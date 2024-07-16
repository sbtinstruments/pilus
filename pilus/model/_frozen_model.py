from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel as snake_to_lower_camel

Derived = TypeVar("Derived", bound="FrozenModel")


class FrozenModel(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        alias_generator=snake_to_lower_camel
    )
