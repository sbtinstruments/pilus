from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, BinaryIO, cast

from ..._magic.signatures import BDR_SIGNATURE
from ...basic import BdrAggregate, BdrAggregateChannel, BdrAggregateSite, FitComplex
from ...errors import PilusDeserializeError
from ...forge import FORGE
from .._chunk import require_single_chunk, stream_chunks
from .._io import read_and_validate_signature
from ._chunks import AhdrChunk, TranChunk


@FORGE.register_deserializer
def from_io(io: Annotated[BinaryIO, "application/vnd.sbt.bdr"]) -> BdrAggregate:
    """Deserialize IO stream into a BDR aggregate."""
    # Signature
    read_and_validate_signature(io, BDR_SIGNATURE)
    # Read header (it must come first)
    header = cast(AhdrChunk, require_single_chunk(io, chunk_models=(AhdrChunk,)))
    # Read data (and interleaved headers, if any)
    #
    # In the IQS specification, there is only a single header in the beginning
    # of the stream. In BDR, however, there may be multiple headers interleaved
    # with the data chunks. We use the most recent header to parse the
    # subsequent data chunks. E.g., to determine which measurement site, that
    # the data belongs to.
    chunk_stream = stream_chunks(  # [1]
        io, chunk_models=(AhdrChunk, TranChunk), channel_names=header.channel_names
    )
    mutable_sites: dict[str, MutableSite] = dict()
    for chunk in chunk_stream:
        if isinstance(chunk, AhdrChunk):
            if header.channel_names != chunk.channel_names:
                raise PilusDeserializeError(
                    "Channel names changed in the middle of the data stream"
                )
            # Remember the latest header
            header = chunk
        elif isinstance(chunk, TranChunk):
            site = _chunks_to_site(ahdr=header, tran=chunk)
            _add_to_sites(mutable_sites, header.site_name, site)
        else:
            assert False
    # Freeze (and validate)
    try:
        sites = _freeze_sites(mutable_sites)
    except ValueError as exc:
        raise PilusDeserializeError(f"Could not freeze sites: {exc}") from exc
    return BdrAggregate(sites=sites)


@dataclass
class _MutableChannel:
    time_start: int
    time_end: int
    transition_fits: list[tuple[FitComplex, ...]]


MutableSite = dict[str, _MutableChannel]


def _chunks_to_site(*, ahdr: AhdrChunk, tran: TranChunk) -> MutableSite:
    return {
        channel_name: _MutableChannel(
            time_start=ahdr.time_start, time_end=ahdr.time_end, transition_fits=[fits]
        )
        for channel_name, fits in tran.site_data.items()
    }


def _add_to_sites(
    sites: dict[str, MutableSite], site_name: str, site: MutableSite
) -> None:
    try:
        current_site = sites[site_name]
    except KeyError:
        sites[site_name] = site
    else:
        # Changes `current_site` in place
        _merge_sites(current_site, site)


def _merge_sites(lhs: MutableSite, rhs: MutableSite) -> None:
    for channel_name, lhs_site in lhs.items():
        try:
            rhs_site = rhs[channel_name]
        except KeyError as exc:
            raise PilusDeserializeError(
                f'Can not merge "{channel_name}" channels since it does not exist in'
                " all sites"
            ) from exc
        # Edit `lhs` in place
        lhs_site.time_end = rhs_site.time_end
        lhs_site.transition_fits.extend(rhs_site.transition_fits)


def _freeze_sites(mutable_sites: dict[str, MutableSite]) -> dict[str, BdrAggregateSite]:
    return {
        site_name: {
            channel_name: BdrAggregateChannel(
                time_start=channel.time_start,
                time_end=channel.time_end,
                # Flatten list of tuples and sort them
                transition_fits=tuple(
                    sorted(fit for fits in channel.transition_fits for fit in fits)
                ),
            )
            for channel_name, channel in site.items()
        }
        for site_name, site in mutable_sites.items()
    }
