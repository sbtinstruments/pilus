from __future__ import annotations

from typing import Any, Type, TypeVar

from pydantic import BaseModel

from ..formats.json import from_json_obj

Derived = TypeVar("Derived", bound="FrozenModel")


class FrozenModel(BaseModel):
    class Config:  # pylint: disable=too-few-public-methods
        frozen = True

    @classmethod
    def parse_obj(cls: Type[Derived], obj: Any) -> Derived:
        return from_json_obj(cls, obj)
