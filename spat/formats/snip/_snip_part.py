from typing import Generic, TypeVar

from pydantic import BaseModel

from ._snip_part_metadata import SnipPartMetadata

T = TypeVar("T")


class SnipPart(BaseModel, Generic[T]):
    """Part (parsed file) of a snip."""

    value: T
    metadata: SnipPartMetadata

    class Config:  # pylint: disable=too-few-public-methods
        frozen = True
