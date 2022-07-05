from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ._chunks import (
    ChannelData,
    ChannelHeader,
    IdatChunk,
    IhdrChunk,
    SiteData,
    SiteHeader,
)


@dataclass(frozen=True)
class IqsAggregateChannel(ChannelData, ChannelHeader):
    """Aggregation of header and data chunks for a single channel."""


IqsAggregateSite = dict[str, IqsAggregateChannel]


@dataclass(frozen=True)
class IqsAggregate:
    """Aggregation of header and data chunks."""

    start_time: datetime
    duration_ns: int
    sites: dict[str, IqsAggregateSite]

    @classmethod
    def from_chunks(cls, ihdr: IhdrChunk, idat: IdatChunk) -> IqsAggregate:
        """Construct an instance from the given IHDR and (merged) IDAT chunks.

        We assume that the given chunks follow the same site-channel hierarchy.
        """
        aggregate_sites: dict[str, IqsAggregateSite] = dict()
        for site_name, data_site in idat.sites.items():
            site_header = ihdr[site_name]
            aggregate_site: IqsAggregateSite = dict()
            for channel_name, data_channel in data_site.items():
                channel_header = site_header[channel_name]
                aggregate_channel = IqsAggregateChannel(
                    channel_header.time_step_ns,
                    channel_header.byte_depth,
                    channel_header.max_amplitude,
                    data_channel.re,
                    data_channel.im,
                )
                aggregate_site[channel_name] = aggregate_channel
            aggregate_sites[site_name] = aggregate_site
        return cls(idat.start_time, idat.duration_ns, aggregate_sites)

    def to_chunks(self) -> tuple[IhdrChunk, IdatChunk]:
        """Convert this instance into an IHDR and an IDAT chunk."""
        return (self.to_ihdr(), self.to_idat())

    def to_idat(self) -> IdatChunk:
        """Return the data-specific parts of this instance as an IDAT chunk."""
        idat_sites: dict[str, SiteData] = dict()
        for site_name, site in self.sites.items():
            idat_site: SiteData = dict()
            for channel_name, channel in site.items():
                idat_channel = ChannelData(channel.re, channel.im)
                idat_site[channel_name] = idat_channel
            idat_sites[site_name] = idat_site
        return IdatChunk(self.start_time, self.duration_ns, idat_sites)

    def to_ihdr(self) -> IhdrChunk:
        """Return the header-specific parts of this instance as an IHDR chunk."""
        ihdr_sites: dict[str, SiteHeader] = dict()
        for site_name, site in self.sites.items():
            ihdr_site: SiteHeader = dict()
            for channel_name, channel in site.items():
                ihdr_channel = ChannelHeader(
                    channel.time_step_ns, channel.byte_depth, channel.max_amplitude
                )
                ihdr_site[channel_name] = ihdr_channel
            ihdr_sites[site_name] = ihdr_site
        return IhdrChunk(ihdr_sites)
