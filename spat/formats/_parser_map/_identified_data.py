from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Union


@dataclass(frozen=True)
class IdentifiedBase:
    """Base class for an identified resource."""

    media_type: str


@dataclass(frozen=True)
class IdentifiedPath(IdentifiedBase):
    """File or directory path identified by it's media type."""

    path: Path


@dataclass(frozen=True)
class IdentifiedIo(IdentifiedBase):
    """Binary IO identified by it's media type."""

    io: BinaryIO


@dataclass(frozen=True)
class IdentifiedData(IdentifiedBase):
    """Raw binary data identified by it's media type."""

    data: bytes


IdentifiedResource = Union[IdentifiedPath, IdentifiedIo, IdentifiedData]
