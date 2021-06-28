from dataclasses import dataclass, replace
from datetime import datetime
from typing import Optional

from ..formats import register_merger, register_parsers, wave


@dataclass(frozen=True)
class Wave:
    """Linear pulse-code modulated (LPCM) signal stored in memmory."""

    byte_depth: int
    time_step_ns: int
    data: bytes = bytes()
    start_time: Optional[datetime] = None

    def __post_init__(self) -> None:
        if len(self.data) % self.byte_depth != 0:
            raise ValueError("Data length must be a multiple of the byte depth.")

    def __len__(self) -> int:
        """Return the logical length of this wave.

        Logical, in the sense that it takes the byte depth into account.
        I.e., it's not just the raw byte count.
        """
        return len(self.data) // self.byte_depth


register_parsers("audio/vnd.wave", from_io=lambda io: wave.from_io(Wave, io))


from ._wave_meta import WaveMeta


def merge_wave_and_wave_meta(wave: Wave, meta: WaveMeta) -> Wave:
    return replace(wave, start_time=datetime(1989, 8, 17))


register_merger(merge_wave_and_wave_meta)
