from typing import BinaryIO, Optional

from ...._magic.signatures import IQS_SIGNATURE
from ..._model import IqsAggregate, IqsChannelData, IqsChannelHeader
from .._chunk import write_chunk
from .._io import write_signature
from ._chunks import IdatChunk, IhdrChunk, SdatChunk, ShdrChunk, SiteData, SiteHeader
from ._iqs_globals import IqsVersion


def to_io(
    aggregate: IqsAggregate,
    io: BinaryIO,
    *,
    version: IqsVersion = IqsVersion.V2_0_0,
    site_to_keep: Optional[str] = None,
) -> None:
    """Serialize IQS aggregate to the IO stream.

    May raise:
      * `PilusSerializeError` or one of its derivatives.
      * `RuntimeError` if the platform doesn't natively support 4-byte integers.
      * `ValueError` if the function arguments are not compatible.
    """
    write_signature(io, IQS_SIGNATURE)
    ihdr, idat = _aggregate_to_chunks(aggregate)
    if version is IqsVersion.V2_0_0:
        write_chunk(io, ihdr)
        write_chunk(io, idat)
    elif version is IqsVersion.V1_0_0:
        if site_to_keep is None:
            raise ValueError(
                "You must specify `site_to_keep` when you target "
                "version 1.0.0 of the IQS specification."
            )
        write_chunk(io, ShdrChunk.from_ihdr(ihdr, site_to_keep=site_to_keep))
        write_chunk(io, SdatChunk.from_idat(idat, site_to_keep=site_to_keep))
    else:
        assert False


def _aggregate_to_chunks(aggregate: IqsAggregate) -> tuple[IhdrChunk, IdatChunk]:
    """Convert aggregate into an IHDR and an IDAT chunk."""
    return (_aggregate_to_ihdr(aggregate), _aggregate_to_idat(aggregate))


def _aggregate_to_idat(aggregate: IqsAggregate) -> IdatChunk:
    """Return the data-specific parts of the aggregate as an IDAT chunk."""
    idat_sites: dict[str, SiteData] = dict()
    for site_name, site in aggregate.sites.items():
        idat_site: SiteData = dict()
        for channel_name, channel in site.items():
            idat_channel = IqsChannelData(channel.re, channel.im)
            idat_site[channel_name] = idat_channel
        idat_sites[site_name] = idat_site
    return IdatChunk(aggregate.start_time, aggregate.duration_ns, idat_sites)


def _aggregate_to_ihdr(aggregate: IqsAggregate) -> IhdrChunk:
    """Return the header-specific parts of the aggregate as an IHDR chunk."""
    ihdr_sites: dict[str, SiteHeader] = dict()
    for site_name, site in aggregate.sites.items():
        ihdr_site: SiteHeader = dict()
        for channel_name, channel in site.items():
            ihdr_channel = IqsChannelHeader(
                channel.time_step_ns, channel.byte_depth, channel.max_amplitude
            )
            ihdr_site[channel_name] = ihdr_channel
        ihdr_sites[site_name] = ihdr_site
    return IhdrChunk(ihdr_sites)
