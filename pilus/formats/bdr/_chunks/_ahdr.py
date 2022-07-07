from __future__ import annotations

from dataclasses import dataclass
from typing import Any, BinaryIO, ClassVar

from ..._io import read_int, read_terminated_string


@dataclass(frozen=True)
class AhdrChunk:
    """Used to interpret the subsequent data chunks."""

    type_: ClassVar[bytes] = b"AHDR"

    site_name: str
    channel_names: tuple[str, ...]
    time_start: int
    time_end: int

    @classmethod
    def from_io(cls, io: BinaryIO, **kwargs: Any) -> AhdrChunk:
        """Deserialize the IO stream into an AHDR chunk.

        May raise `BdrError` or one of its derivatives.
        """
        # Read site_name[*chr[256]] - fixed 256 bytes length with trailing zeros
        site_name = read_terminated_string(io, 256)
        # Read channels[uint32]
        channels = read_int(io, 4)
        channel_names = tuple(read_terminated_string(io, 256) for _ in range(channels))
        # times[uint64] - times given in uSeconds
        time_start = read_int(io, 8)
        time_end = read_int(io, 8)
        return AhdrChunk(
            site_name=site_name,
            channel_names=channel_names,
            time_start=time_start,
            time_end=time_end,
        )
