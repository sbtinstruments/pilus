from __future__ import annotations

from pathlib import Path
from typing import BinaryIO, ClassVar, Type, TypeVar, Union, cast

from pydantic import BaseModel

from ..formats import IdentifiedIo, IdentifiedPath, SpatError, parse
from ._from_funcs import from_json_data

Derived = TypeVar("Derived", bound="Model")


class Model(BaseModel):

    json_media_type: ClassVar[str]

    @classmethod
    def from_file(cls, file: Path) -> Derived:
        if file.suffix != ".json":
            raise SpatError(
                'Can only parse JSON files but got extension: "{file.suffix}"'
            )
        return cast(Derived, parse(IdentifiedPath(cls._get_json_media_type(), file)))

    @classmethod
    def from_json_io(cls, io: BinaryIO) -> Derived:
        return cast(Derived, parse(IdentifiedIo(cls._get_json_media_type(), io)))

    @classmethod
    def from_json_data(cls: Type[Derived], data: Union[str, bytes]) -> Derived:
        return from_json_data(cls, data)

    @classmethod
    def _get_json_media_type(cls) -> str:
        try:
            return cls.json_media_type
        except AttributeError as exc:
            raise SpatError(
                f'The "{cls.__name__}" model does not have an associated '
                "JSON-based media type"
            ) from exc

    class Config:
        frozen = True
