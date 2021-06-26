from typing import Generic, TypeVar

from ._snip_part_metadata import SnipPartMetadata

T = TypeVar("T")


class SnipPart(SnipPartMetadata, Generic[T]):
    value: T

    class Config:
        frozen = True
