from typing import Generic, TypeVar

from pydantic import BaseModel

from ._snip_part_metadata import SnipPartMetadata

T = TypeVar("T")


class SnipPart(BaseModel, Generic[T], frozen=True):
    """Part (deserialized file) of a snip."""

    value: T
    metadata: SnipPartMetadata
