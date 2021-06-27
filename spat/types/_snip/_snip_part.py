from typing import Generic, TypeVar

from pydantic import BaseModel

from ._snip_part_metadata import SnipPartMetadata

T = TypeVar("T")


class SnipPart(BaseModel, Generic[T]):
    value: T
    metadata: SnipPartMetadata

    class Config:
        frozen = True
