from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Type, TypeVar, cast

from pydantic import BaseModel

from ..formats import PilusError
from ..formats.registry import Resource, deserialize

Derived = TypeVar("Derived", bound="Model")


class Model(BaseModel):
    """Immutable pydantic model with auto-generated serialization/deserialization."""

    class Config:  # pylint: disable=too-few-public-methods
        frozen = True

    # Override this media type list in a derived class to enable the
    # serialization/deserialization methods. E.g., via the
    # `add_media_type` operator.
    media_types: ClassVar[tuple[str, ...]] = tuple()

    @classmethod
    def from_file(cls: Type[Derived], file: Path) -> Derived:
        """Deserialize file into an instance of this class.

        This method is disabled by default. You can enable it if you associate this
        class with a media type. E.g., via the `add_media_type` decorator.
        """
        if file.suffix == ".json":
            return cls.from_json(file)
        raise PilusError(
            'Can only deserialize JSON files but got extension: "{file.suffix}"'
        )

    @classmethod
    def from_json(cls: Type[Derived], resource: Resource) -> Derived:
        """Deserialize resource (file, IO stream, data) into an instance of this class.

        This method is disabled by default. You can enable it if you associate this
        class with a media type. E.g., via the `add_media_type` decorator.
        """
        return cast(Derived, deserialize(cls.json_media_type(), resource))

    @classmethod
    def json_media_type(cls) -> str:
        """Return the first media type with a JSON suffix ("+json" at the end).

        Raises `PilusError` if there is no such media type.
        """
        try:
            return next(mt for mt in cls.media_types if mt.endswith("+json"))
        except StopIteration as exc:
            raise PilusError(
                f'The "{cls.__name__}" model does not have an associated '
                "JSON-suffixed media type"
            ) from exc
