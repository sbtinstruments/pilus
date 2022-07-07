from __future__ import annotations

from dataclasses import dataclass
from typing import Any, BinaryIO, ClassVar, Protocol, runtime_checkable


@dataclass(frozen=True)
class UnidentifiedAncilliaryChunk:
    """Non-critical chunk."""


@runtime_checkable
class ReadableChunk(Protocol):
    """Chunk that you can read from binary IO."""

    type_: ClassVar[bytes]

    @classmethod
    def from_io(cls, io: BinaryIO, **kwargs: Any) -> ReadableChunk:
        ...


class WritableChunk(Protocol):
    """Chunk that you can write to binary IO."""

    type_: ClassVar[bytes]

    def to_io(self, io: BinaryIO) -> None:
        ...

    def data_length(self) -> int:
        ...
