from __future__ import annotations

from dataclasses import dataclass
from os import PathLike
from typing import BinaryIO, Optional

from ._magic import detect_media_type
from ._raw_medium import RawMedium, RawMediumType, is_binary_io_like


@dataclass(frozen=True)
class MediumSpec:
    """Specification of a medium."""

    raw_type: RawMediumType
    media_type: str


@dataclass(frozen=True)
class Medium:
    """Raw medium (path, IO stream, data, etc.) identified by a media type."""

    raw: RawMedium
    media_type: str

    @property
    def spec(self) -> MediumSpec:
        return MediumSpec(raw_type=_type_of_raw(self.raw), media_type=self.media_type)

    @classmethod
    def from_raw(
        cls,
        raw: RawMedium,
        *,
        media_type: Optional[str] = None,
    ) -> Medium:
        if media_type is None:
            media_type = detect_media_type(raw)
        return cls(raw=raw, media_type=media_type)


def _type_of_raw(raw: RawMedium) -> RawMediumType:
    if isinstance(raw, PathLike):
        return PathLike
    if is_binary_io_like(raw):
        return BinaryIO
    if isinstance(raw, bytes):
        return bytes
    assert False, "We should cover all cases of RawMedium"
