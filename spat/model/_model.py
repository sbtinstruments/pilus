from __future__ import annotations

from pathlib import Path
from typing import BinaryIO, ClassVar, Type, TypeVar, cast

from pydantic import BaseModel

from ..formats import IdentifiedData, IdentifiedIo, IdentifiedPath, SpatError, parse

Derived = TypeVar("Derived", bound="Model")


class Model(BaseModel):
    """Immutable pydantic model with auto-generated serialization/deserialization."""

    class Config:
        frozen = True

    # Override this media type list in a derived class to enable the
    # serialization/deserialization methods. E.g., via the
    # `add_media_type` operator.
    media_types: ClassVar[tuple[str, ...]] = tuple()

    @classmethod
    def from_file(cls: Type[Derived], file: Path) -> Derived:
        """Create instance based on the given file.

        This method is disabled by default. You can enable it if you associate this
        class with a media type. E.g., via the `add_media_type` decorator.
        """
        if file.suffix != ".json":
            raise SpatError(
                'Can only parse JSON files but got extension: "{file.suffix}"'
            )
        return cast(Derived, parse(IdentifiedPath(cls.json_media_type(), file)))

    @classmethod
    def from_json_io(cls: Type[Derived], io: BinaryIO) -> Derived:
        """Create instance based on the given binary IO stream.

        This method is disabled by default. You can enable it if you associate this
        class with a media type. E.g., via the `add_media_type` decorator.
        """
        return cast(Derived, parse(IdentifiedIo(cls.json_media_type(), io)))

    @classmethod
    def from_json_data(cls: Type[Derived], data: bytes) -> Derived:
        """Create instance based on the given binary data.

        This method is disabled by default. You can enable it if you associate this
        class with a media type. E.g., via the `add_media_type` decorator.
        """
        return cast(Derived, parse(IdentifiedData(cls.json_media_type(), data)))

    @classmethod
    def json_media_type(cls) -> str:
        """Return the first media type with a JSON suffix ("+json" at the end).

        Raises `SpatError` if there is no such media type.
        """
        try:
            return next(mt for mt in cls.media_types if mt.endswith("+json"))
        except StopIteration as exc:
            raise SpatError(
                f'The "{cls.__name__}" model does not have an associated '
                "JSON-suffixed media type"
            ) from exc
