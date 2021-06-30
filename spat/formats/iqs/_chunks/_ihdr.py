from dataclasses import dataclass
from typing import BinaryIO

from .._io_utilities import read_int, read_terminated_string, skip_data


@dataclass(frozen=True)
class ChannelHeader:
    """Used to interpret raw binary channel data."""

    time_step_ns: int
    byte_depth: int
    max_amplitude: int


SiteHeader = dict[str, ChannelHeader]


@dataclass(frozen=True)
class IhdrChunk:
    """Used to interpret the subsequent IDAT chunks."""

    value: dict[str, SiteHeader]


def read_ihdr(io: BinaryIO) -> IhdrChunk:
    """Deserialize the IO stream into an IHDR chunk.

    May raise `IqsError` or one of its derivatives.
    """
    number_of_sites = read_int(io, 4)
    ihdr_value: dict[str, SiteHeader] = dict()
    for _ in range(number_of_sites):
        site_name = read_terminated_string(io, 256)  # E.g.: "site0"
        number_of_channels = read_int(io, 4)
        site_header: SiteHeader = dict()
        for _ in range(number_of_channels):
            channel_name = read_terminated_string(io, 256)  # E.g.: "hf"
            time_step_ns = read_int(io, 4)
            byte_depth = read_int(io, 1)
            # HACK: Read the first 8 bytes and skip the remaining 56 bytes
            max_amplitude = read_int(io, 8, signed=True)
            skip_data(io, 56)
            # Add channel header to site header
            channel_header = ChannelHeader(time_step_ns, byte_depth, max_amplitude)
            site_header[channel_name] = channel_header
        # Add site header to chunk
        ihdr_value[site_name] = site_header
    return IhdrChunk(ihdr_value)


# def _write_ihdr(io: BinaryIO, iqs: dict) -> None:
#     """Write header chunk."""
#     # write chunk length
#     write_uint32(io, _get_ihdr_b_length(iqs))
#     # write chunk type
#     io.write(b"IHDR")
#     # write nSites
#     write_uint32(io, len(iqs["IHDR"].keys()))
#     for site_name, site in iqs["IHDR"].items():
#         # write site name
#         b_site_name = bytearray(site_name, "utf-8")
#         io.write(b_site_name + bytearray(256 - len(b_site_name)))
#         # write nChannels
#         write_uint32(io, len(site.keys()))
#         for freq_name, freq in site.items():
#             # write freq name
#             b_freq_name = bytearray(freq_name, "utf-8")
#             io.write(b_freq_name + bytearray(256 - len(b_freq_name)))
#             write_uint32(io, freq["sample_time_step"])
#             write_uint8(io, freq["sample_byte_depth"])
#             write_int64(io, freq["sample_max_signal_amplitude"])
#             # HACK: write some bytes to comply with the specs
#             io.write(bytearray(56))

#     # write crc
#     write_uint32(io, 0)


# def _get_ihdr_b_length(iqs: dict) -> int:
#     """Compute IHDR chunk byte length."""
#     site_names = list(iqs["IHDR"].keys())
#     n_sites = len(site_names)
#     n_channels = len(iqs["IHDR"][site_names[0]].keys())
#     return n_sites * (256 + 4 + n_channels * (256 + 4 + 1 + 8 + 56)) + 4
