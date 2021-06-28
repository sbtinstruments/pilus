from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Optional

from ..formats import register_merger, register_parsers, wave
from ._wave_meta import WaveMeta


@dataclass(frozen=True)
class Wave:
    """Linear, pulse-code-modulated (LPCM) signal stored in memmory."""

    byte_depth: int
    time_step_ns: int
    data: bytes = bytes()
    start_time: Optional[datetime] = None

    def __post_init__(self) -> None:
        if len(self.data) % self.byte_depth != 0:
            raise ValueError("Data length must be a multiple of the byte depth.")

    def apply_metadata(self: Wave, meta: WaveMeta) -> Wave:
        """Return a copy of this wave with the given metadata applied."""
        return replace(self, start_time=datetime(1989, 8, 17))

    def __len__(self) -> int:
        """Return the logical length of this wave.

        Logical, in the sense that it takes the byte depth into account.
        I.e., it's not just the raw byte count.
        """
        return len(self.data) // self.byte_depth


register_parsers("audio/vnd.wave", from_io=lambda io: wave.from_io(Wave, io))
register_merger(Wave.apply_metadata)
