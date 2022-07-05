from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, BinaryIO, ClassVar, Optional

from .._errors import IqsError
from .._io_utilities import read_exactly, read_int, write_exactly, write_int
from ._ihdr import IhdrChunk

if TYPE_CHECKING:
    from ._sdat import SdatChunk


@dataclass(frozen=True)
class ChannelData:
    """Raw binary channel data split into complex parts."""

    re: bytes
    im: bytes

    def __post_init__(self) -> None:
        if len(self.re) != len(self.im):
            raise ValueError("The two complex parts must have the same length")


SiteData = dict[str, ChannelData]


@dataclass(frozen=True)
class IdatChunk:
    """LPCM signal data."""

    type_: ClassVar[bytes] = b"IDAT"

    start_time: datetime
    duration_ns: int
    sites: dict[str, SiteData]

    @property
    def end_time(self) -> datetime:
        """Return the time that this chunk ends on (not inclusive)."""
        duration = timedelta(microseconds=self.duration_ns * 1e-3)
        return self.start_time + duration

    @classmethod
    def merge_all(
        cls,
        *chunks: IdatChunk,
        ihdr: IhdrChunk,
        contiguous_tolerance: Optional[timedelta] = None,
    ) -> IdatChunk:
        """Merge all the chunks into one.

        This function assumes that the given chunks follow the same site and channel
        hierarchy.
        """
        # Early out if there are no chunks
        if not chunks:
            raise ValueError("Can't merge empty sequence of chunks")
        first_chunk = chunks[0]
        # Early out if the chunks overlap or underlap
        cls.raise_if_not_contiguous(*chunks, tolerance=contiguous_tolerance)
        # Compute the total duration. We need this to pre-allocate memory
        # inside the loop.
        # Note that `total_duration_ns` is NOT a multiple of `time_step_ns`
        # at this point. We account for this fact inside the for loop
        total_duration_ns = int(  # [1]
            (chunks[-1].end_time - chunks[0].start_time).total_seconds() * 1e9
        )
        # Go through the site/channel hierarchy based on that of the first chunk.
        # We assume that the subsequent chunks follow the same hierarchy.
        merged_value: dict[str, SiteData] = dict()
        for site_name, site_data in first_chunk.sites.items():
            merged_site: SiteData = dict()
            for channel_name in site_data:
                channel_header = ihdr[site_name][channel_name]
                # Make sure that the rough computation of `total_duration_ns` at [1]
                # is a multiple of `time_step_ns`.
                # Note that this subtraction only has effect the first time. The
                # remainder is always zero on subsequent iterations (see [2]).
                total_duration_ns -= total_duration_ns % channel_header.time_step_ns
                assert total_duration_ns % channel_header.time_step_ns == 0  # [2]
                total_logical_length = total_duration_ns // channel_header.time_step_ns
                total_byte_length = total_logical_length * channel_header.byte_depth
                # We pre-allocate the memory up front. This avoids a lot of memory
                # allocations inside the for loop itself.
                merged_re = bytearray(total_byte_length)
                merged_im = bytearray(total_byte_length)
                for chunk in chunks:
                    # We compute `offset` based on the chunk's start time to
                    # account for non-overlapping chunks. E.g., if the system time
                    # suddenly jumped ahead/behind during the IQS save.
                    start_delta = chunk.start_time - first_chunk.start_time
                    start_delta_ns = start_delta.total_seconds() * 1e9
                    offset = (
                        int(start_delta_ns // channel_header.time_step_ns)
                        * channel_header.byte_depth
                    )
                    site = chunk.sites[site_name]
                    channel = site[channel_name]
                    length = len(channel.re)
                    assert length == len(channel.im)
                    # [3] Note that `bytearray` is pretty lenient about splicing:
                    #
                    #   >>> x = bytearray(3)
                    #   >>> len(x)
                    #   3
                    #   >>> x[1:7] = bytes(7)
                    #   >>> len(x)
                    #   8
                    #
                    # In other words, `bytearray` allows us not only to modify
                    # its contents but also to go beyond the existing bounds.
                    merged_re[offset : offset + length] = channel.re
                    merged_im[offset : offset + length] = channel.im
                # Bound the data because the last chunk may extend a bit beyond
                # the `total_byte_length`. We expect this to occur since we round
                # down at [1] and [2] and because of [3].
                merged_re_bound = merged_re[0:total_byte_length]
                merged_im_bound = merged_im[0:total_byte_length]
                merged_channel = ChannelData(
                    bytes(merged_re_bound),
                    bytes(merged_im_bound),
                )
                # Check that our bounds hold
                assert len(merged_channel.re) == total_byte_length
                assert len(merged_channel.im) == total_byte_length
                merged_site[channel_name] = merged_channel
            merged_value[site_name] = merged_site
        return cls(first_chunk.start_time, total_duration_ns, merged_value)

    @classmethod
    def raise_if_not_contiguous(
        cls,
        *chunks: IdatChunk,
        tolerance: Optional[timedelta] = None,
    ) -> None:
        """Raise an `IqsError` error if the given chunks are not adjoined in time."""
        # Default arguments
        if tolerance is None:
            tolerance = timedelta(microseconds=1)
        # Early out if there are no chunks
        if not chunks:
            raise ValueError("Can't check empty sequence of chunks")
        previous_chunk = chunks[0]
        for chunk in chunks[1:]:
            delta = previous_chunk.end_time - chunk.start_time
            if abs(delta) > tolerance:
                delta_us = delta.total_seconds() * 1e6
                threshold_us = tolerance.total_seconds() * 1e6
                raise IqsError(
                    f"The chunks are {delta_us:.2f} µs apart. "
                    f"The threshold is {threshold_us:.2f} µs."
                )
            previous_chunk = chunk

    @classmethod
    def from_sdat(
        cls, sdat: "SdatChunk", *, site_name: str, time_step_ns: int
    ) -> IdatChunk:
        """Convert the SDAT chunk into an IDAT chunk.

        May raise:
          * `RuntimeError` if the platform doesn't natively support 4-byte integers.
        """
        # We de-interleave the data first
        format_string = "i"  # 4-byte integer
        interleaved = memoryview(sdat.interleaved_data).cast(format_string)
        if interleaved.itemsize != 4:
            raise RuntimeError("The native integer size must be 4 bytes")
        hf_re = interleaved[0::4].tobytes()
        hf_im = interleaved[1::4].tobytes()
        lf_re = interleaved[2::4].tobytes()
        lf_im = interleaved[3::4].tobytes()
        hf_channel = ChannelData(hf_re, hf_im)
        lf_channel = ChannelData(lf_re, lf_im)
        site: SiteData = {
            "hf": hf_channel,
            "lf": lf_channel,
        }
        sites: dict[str, SiteData] = {site_name: site}
        duration_ns = time_step_ns * len(hf_re) // 4
        return cls(sdat.start_time, duration_ns, sites)

    @classmethod
    def from_io(cls, io: BinaryIO, *, ihdr: IhdrChunk) -> IdatChunk:
        """Deserialize the IO stream into an IDAT chunk.

        May raise `IqsError` or one of its derivatives.
        """
        timestamp_us = read_int(io, 8)
        duration_ns = read_int(io, 8)

        idat_value: dict[str, SiteData] = dict()
        for site_name, site_header in ihdr.items():
            site_data: SiteData = dict()
            for channel_name, channel_header in site_header.items():
                if duration_ns % channel_header.time_step_ns != 0:
                    raise IqsError(
                        "IDAT duration is not a multiple of the IHDR time step"
                    )
                logical_length = duration_ns // channel_header.time_step_ns
                byte_length = logical_length * channel_header.byte_depth
                re_data = read_exactly(io, byte_length)
                im_data = read_exactly(io, byte_length)
                # Add channel data to site data
                channel_data = ChannelData(re_data, im_data)
                site_data[channel_name] = channel_data
            # Add site header to chunk
            idat_value[site_name] = site_data
        start_time = datetime.fromtimestamp(timestamp_us * 1e-6)
        return IdatChunk(start_time, duration_ns, idat_value)

    def to_io(self, io: BinaryIO) -> None:
        """Serialize this chunk into the IO stream.

        This only returns the "data" and not the "length", "type", or "CRC".

        May raise `IqsError` or one of its derivatives.
        """
        timestamp_us = int(self.start_time.timestamp() * 1e6)
        write_int(io, timestamp_us, 8)
        write_int(io, self.duration_ns, 8)
        for site in self.sites.values():
            for channel in site.values():
                write_exactly(io, channel.re)
                write_exactly(io, channel.im)

    def data_length(self) -> int:
        """Return the byte size of this chunk in serialized form."""
        # Timestamp and duration
        result = 8 + 8
        # Actual data
        for site in self.sites.values():
            for channel in site.values():
                result += len(channel.re) + len(channel.im)
        return result
