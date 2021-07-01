from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, BinaryIO, ClassVar

from .._errors import IqsError
from .._io_utilities import read_int, write_int

if TYPE_CHECKING:
    from ._ihdr import IhdrChunk


@dataclass(frozen=True)
class ShdrChunk:
    """Used to interpret the subsequent SDAT chunks."""

    type_: ClassVar[bytes] = b"SHDR"

    time_step_ns: int
    max_amplitude: int

    @classmethod
    def from_ihdr(cls, ihdr: "IhdrChunk", *, site_to_keep: str) -> ShdrChunk:
        """Convert the IHDR chunk into an SHDR chunk.

        May raise `IqsError` or one of its derivatives.
        """
        try:
            site = ihdr[site_to_keep]
        except KeyError as exc:
            raise IqsError(f'No such site: "{site_to_keep}"') from exc
        channel_headers = frozenset(site.values())
        # Early out if the channels are not in the same format
        if len(channel_headers) > 1:
            raise IqsError("Channels are heterogenous")
        channel_header = next(iter(channel_headers))
        return cls(channel_header.time_step_ns, channel_header.max_amplitude)

    @classmethod
    def from_io(cls, io: BinaryIO) -> ShdrChunk:
        """Deserialize the IO stream into an SHDR chunk.

        May raise `IqsError` or one of its derivatives.
        """
        time_step_ns = read_int(io, 4)
        max_amplitude = read_int(io, 4)
        return cls(time_step_ns, max_amplitude)

    def to_io(self, io: BinaryIO) -> None:
        """Serialize this chunk to the IO stream.

        This only returns the "data" and not the "length", "type", or "CRC".

        May raise `IqsError` or one of its derivatives.
        """
        write_int(io, self.time_step_ns, 4)
        write_int(io, self.max_amplitude, 4)

    def data_length(self) -> int:
        """Return the byte size of this chunk in serialized form."""
        return 8
