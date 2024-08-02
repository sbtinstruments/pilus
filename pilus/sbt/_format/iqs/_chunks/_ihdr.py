from __future__ import annotations

from typing import TYPE_CHECKING, Any, BinaryIO, ClassVar

from ...._model import IqsChannelHeader
from ..._io import read_int, read_terminated_string, write_int, write_terminated_string

if TYPE_CHECKING:
    from ._shdr import ShdrChunk


SiteHeader = dict[str, IqsChannelHeader]


class IhdrChunk(dict[str, SiteHeader]):
    """Used to interpret the subsequent IDAT chunks."""

    type_: ClassVar[bytes] = b"IHDR"

    @classmethod
    def from_shdr(cls, shdr: "ShdrChunk", *, site_name: str) -> IhdrChunk:
        """Convert the SHDR chunk into an IHDR chunk.

        Doesn't raise any exceptions.
        """
        channel_header = IqsChannelHeader(shdr.time_step_ns, 4, shdr.max_amplitude)
        site: SiteHeader = {"hf": channel_header, "lf": channel_header}
        sites: dict[str, SiteHeader] = {site_name: site}
        return cls(sites)

    @classmethod
    def from_io(cls, io: BinaryIO, **kwargs: Any) -> IhdrChunk:
        """Deserialize the IO stream into an IHDR chunk.

        May raise `IqsError` or one of its derivatives.
        """
        number_of_sites = read_int(io, 4)
        sites: dict[str, SiteHeader] = dict()
        for _ in range(number_of_sites):
            site_name = read_terminated_string(io, 256)  # E.g.: "site0"
            number_of_channels = read_int(io, 4)
            site_header: SiteHeader = dict()
            for _ in range(number_of_channels):
                channel_name = read_terminated_string(io, 256)  # E.g.: "hf"
                time_step_ns = read_int(io, 4)
                byte_depth = read_int(io, 1)
                # Yes, this is actually a 64-byte integer (not a 64-bit integer).
                # This is by design since byte depth theoretically goes to 64
                # (though it's usually only 4).
                max_amplitude = read_int(io, 64, signed=True)
                # Add channel header to site header
                channel_header = IqsChannelHeader(
                    time_step_ns, byte_depth, max_amplitude
                )
                site_header[channel_name] = channel_header
            # Add site header to chunk
            sites[site_name] = site_header
        return cls(sites)

    def to_io(self, io: BinaryIO) -> None:
        """Serialize this chunk to the IO stream.

        This only returns the "data" and not the "length", "type", or "CRC".

        May raise `IqsError` or one of its derivatives.
        """
        write_int(io, len(self), 4)
        for site_name, site in self.items():
            write_terminated_string(io, site_name, 256)
            write_int(io, len(site), 4)
            for channel_name, channel in site.items():
                write_terminated_string(io, channel_name, 256)
                write_int(io, channel.time_step_ns, 4)
                write_int(io, channel.byte_depth, 1)
                write_int(io, channel.max_amplitude, 64, signed=True)

    def data_length(self) -> int:
        """Return the byte size of this chunk in serialized form."""
        # Site names and length
        result = len(self) * 256 + 4
        # Channel names, length
        result += sum(4 + len(site) * (256 + 4 + 1 + 64) for site in self.values())
        return result
