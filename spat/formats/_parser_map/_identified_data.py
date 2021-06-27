from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Union


@dataclass(frozen=True)
class _IdentifiedBase:
    """Base class for an identified resource."""

    media_type: str


@dataclass(frozen=True)
class IdentifiedPath(_IdentifiedBase):
    """File or directory path identified by its media type."""

    path: Path


@dataclass(frozen=True)
class IdentifiedIo(_IdentifiedBase):
    """Binary IO identified by its media type."""

    io: BinaryIO


@dataclass(frozen=True)
class IdentifiedData(_IdentifiedBase):
    """Binary data identified by its media type."""

    data: bytes


IdentifiedResource = Union[IdentifiedPath, IdentifiedIo, IdentifiedData]
