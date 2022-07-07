from pathlib import Path
from typing import BinaryIO, Optional, Type, TypeVar

from .._magic import Medium
from ._global_forge import FORGE

Derived = TypeVar("Derived", bound="ForgeIO")


# Ideally, `ForgeIO` would be a class decorator instead. Unfortunately, the current
# selection of type tooling has very limited support for class decorators.
# In practice, the type tooling is unable to pick up that you add a new method
# to the class (which is the whole purpose of `ForgeIO`). Therefore, we use a
# class instead (just like pydantic chose to do).
class ForgeIO:
    """Serialization/deserialization via a `Forge` instance."""

    @classmethod
    def from_io(
        cls: Type[Derived], io: BinaryIO, *, media_type: Optional[str] = None
    ) -> Derived:
        """Deserialize IO stream into an instance of this class."""
        input_medium = Medium.from_raw(io, media_type=media_type)
        return FORGE.deserialize(input_medium, cls)

    @classmethod
    def from_file(
        cls: Type[Derived], file: Path, *, media_type: Optional[str] = None
    ) -> Derived:
        """Deserialize file into an instance of this class."""
        input_medium = Medium.from_raw(file, media_type=media_type)
        return FORGE.deserialize(input_medium, cls)
