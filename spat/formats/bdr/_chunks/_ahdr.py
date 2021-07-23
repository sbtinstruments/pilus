from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, BinaryIO, ClassVar, Optional

from .._errors import BdrError
from ...iqs._io_utilities import read_exactly, read_int, read_terminated_string


@dataclass(frozen=True)
class AhdrChunk:
    """LPCM signal data."""

    type_: ClassVar[bytes] = b"AHDR"
    site_name : str
    channel_name: list[str]
    time_start: int
    time_end: int

    @classmethod
    def from_io(cls, io: BinaryIO) -> AhdrChunk:
        """Deserialize the IO stream into an IDAT chunk.

        May raise `BdrError` or one of its derivatives.
        """
        # read site_name[*chr[256]] - fixed 256 bytes length with trailing zeros
        site_name = read_terminated_string(io, 256)
        # read channels[uint32]
        channels = read_int(io, 4)
        # times[uint64] - times given in uSeconds
        channel_names = []
        for i in range(channels):
            channel_names.append(read_terminated_string(io, 256))

        time_start = read_int(io, 8)
        time_end = read_int(io, 8)

        return AhdrChunk(site_name, channel_names, time_start, time_end)