from __future__ import annotations

from pathlib import Path
from typing import Type, TypeVar, Union

from pydantic import BaseModel

from ._from_funcs import from_file, from_json_data

Derived = TypeVar("Derived", bound="Model")


class Model(BaseModel):
    class Config:
        frozen = True

    @classmethod
    def from_file(cls: Type[Derived], path: Path) -> Derived:
        return from_file(cls, path)

    @classmethod
    def from_json_data(cls: Type[Derived], data: Union[str, bytes]) -> Derived:
        return from_json_data(cls, data)
