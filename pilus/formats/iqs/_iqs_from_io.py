from datetime import timedelta
from typing import Annotated, BinaryIO, Optional, Union, cast, get_args

from ..._magic.signatures import IQS_SIGNATURE
from ...basic import IqsAggregate, IqsAggregateChannel, IqsAggregateSite
from ...errors import PilusDeserializeError
from ...forge import FORGE
from .._chunk import require_single_chunk, stream_chunks
from .._io import read_and_validate_signature
from ._chunks import DataChunk, HeaderChunk, IdatChunk, IhdrChunk, SdatChunk, ShdrChunk


@FORGE.register_deserializer
def from_io(
    io: Annotated[BinaryIO, "application/vnd.sbt.iqs"],
    *,
    version_1_0_0_site_name: Optional[str] = None,
    contiguous_tolerance: Optional[timedelta] = None,
) -> IqsAggregate:
    """Deserialize IO stream into an IQS aggregate.

    May raise `PilusDeserializeError` or one of its derivatives.

    Converts chunks from version 1.0.0 of the IQS specification into the
    corresponding chunks from version 2.0.0.

    Merges all data chunks (IDAT or SDAT) into a single chunk. This way, all the
    raw binary data is contiguous.
    """
    # Default arguments
    if version_1_0_0_site_name is None:
        version_1_0_0_site_name = "site0"
    # Signature
    read_and_validate_signature(io, IQS_SIGNATURE)
    # Read header (it must come first).
    #
    # We save the header chunk so that we can pass it to `read_chunk`
    # in the subsequent iterations. We use it internally to deserialize
    # the data chunk(s).
    header = cast(
        HeaderChunk, require_single_chunk(io, chunk_models=get_args(HeaderChunk))
    )
    # Read data
    data = cast(
        list[DataChunk],
        list(stream_chunks(io, chunk_models=get_args(DataChunk), header=header)),
    )
    if not data:
        raise PilusDeserializeError("No data chunks.")
    # Convert everything to the version 2.0.0 chunk types (IHDR and IDAT)
    ihdr = _ensure_ihdr(header, site_name=version_1_0_0_site_name)
    idats = (
        _ensure_idat(chunk, site_name=version_1_0_0_site_name, header=header)
        for chunk in data
    )
    # Merge all data together
    merged_idat = IdatChunk.merge_all(
        *idats, ihdr=ihdr, contiguous_tolerance=contiguous_tolerance
    )
    return _chunks_to_aggregate(ihdr, merged_idat)


def _chunks_to_aggregate(ihdr: IhdrChunk, idat: IdatChunk) -> IqsAggregate:
    """Construct an aggregate from the given IHDR and (merged) IDAT chunks.

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
    return IqsAggregate(
        start_time=idat.start_time, duration_ns=idat.duration_ns, sites=aggregate_sites
    )


def _ensure_ihdr(header: HeaderChunk, *, site_name: str) -> IhdrChunk:
    # Early out if we already got an IHDR chunk
    if isinstance(header, IhdrChunk):
        return header
    return IhdrChunk.from_shdr(header, site_name=site_name)


def _ensure_idat(
    chunk: Union[SdatChunk, IdatChunk], site_name: str, header: Optional[HeaderChunk]
) -> IdatChunk:
    # Early out if we already got an IDAT chunk
    if isinstance(chunk, IdatChunk):
        return chunk
    # Convert SDAT to IDAT
    if not isinstance(header, ShdrChunk):
        raise PilusDeserializeError(
            "Need an SHDR chunk to convert an SDAT chunk to IDAT"
        )
    return IdatChunk.from_sdat(
        chunk,
        site_name=site_name,
        time_step_ns=header.time_step_ns,
    )
