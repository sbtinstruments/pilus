from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, BinaryIO, ClassVar

from .._errors import IqsError
from .._io_utilities import (
    read_int,
    read_terminated_string,
    write_exactly,
    write_int,
    write_terminated_string,
)

if TYPE_CHECKING:
    from ._idat import IdatChunk


@dataclass(frozen=True)
class SdatChunk:
    """Used to interpret the subsequent SDAT chunks."""

    type_: ClassVar[bytes] = b"SDAT"

    start_time: datetime
    interleaved_data: bytes

    @classmethod
    def from_idat(cls, idat: "IdatChunk", *, site_to_keep: str) -> SdatChunk:
        """Convert the IDAT chunk into an SDAT chunk.

        May raise:
          * `IqsError` or one of its derivatives.
          * `RuntimeError` if the platform doesn't natively support 4-byte integers.
        """
        try:
            site = idat.sites[site_to_keep]
        except KeyError as exc:
            raise IqsError(f'No such site: "{site_to_keep}"') from exc
        if len(site) > 2:
            raise IqsError("Too many channels in the site")
        try:
            hf_channel = site["hf"]
            lf_channel = site["lf"]
        except KeyError as exc:
            raise IqsError("Couldn't find the HF and LF channels") from exc
        # Interleave channels
        buffer = bytearray(len(hf_channel.re) * 4)  # 4 channels
        format_string = "i"  # 4-byte integer
        interleaved = memoryview(buffer).cast(format_string)
        if interleaved.itemsize != 4:
            raise RuntimeError("The native integer size must be 4 bytes")
        hf_re = memoryview(hf_channel.re).cast(format_string)
        hf_im = memoryview(hf_channel.im).cast(format_string)
        lf_re = memoryview(lf_channel.re).cast(format_string)
        lf_im = memoryview(lf_channel.im).cast(format_string)
        interleaved[0::4] = hf_re
        interleaved[1::4] = hf_im
        interleaved[2::4] = lf_re
        interleaved[3::4] = lf_im
        return cls(idat.start_time, bytes(interleaved))

    def to_io(self, io: BinaryIO) -> None:
        """Serialize this chunk to the IO stream.

        This only returns the "data" and not the "length", "type", or "CRC".

        May raise `IqsError` or one of its derivatives.
        """
        timestamp_us = int(self.start_time.timestamp() * 1e6)
        write_int(io, timestamp_us, 8)
        write_exactly(io, self.interleaved_data)

    def data_length(self) -> int:
        """Return the byte size of this chunk in serialized form."""
        return 8 + len(self.interleaved_data)
