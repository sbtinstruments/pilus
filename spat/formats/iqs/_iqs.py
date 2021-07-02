from enum import Enum, auto
from typing import BinaryIO, Optional, Union

from ._aggregate import IqsAggregate
from ._chunks import (
    DataChunk,
    HeaderChunk,
    IdatChunk,
    IhdrChunk,
    SdatChunk,
    ShdrChunk,
    UnidentifiedAncilliaryChunk,
    read_chunk,
    write_chunk,
)
from ._errors import IqsError
from ._signature import read_and_validate_signature, write_signature


class IqsVersion(Enum):
    """Version of the IQS specification."""

    V1_0_0 = auto()
    V2_0_0 = auto()


def from_io(
    io: BinaryIO, *, version_1_0_0_site_name: Optional[str] = None
) -> Optional[IqsAggregate]:
    """Deserialize IO stream into an IQS aggregate.

    May raise `IqsError` or one of its derivatives.

    Converts chunks from version 1.0.0 of the IQS specification into the
    corresponding chunks from version 2.0.0.

    Merges all data chunks (IDAT or SDAT) into a single chunk. This way, all the
    raw binary data is contiguous.
    """
    # Default arguments
    if version_1_0_0_site_name is None:
        version_1_0_0_site_name = "site0"
    # Signature
    read_and_validate_signature(io)
    # Read header and data
    header: Optional[HeaderChunk] = None
    data: list[DataChunk] = list()
    while chunk := read_chunk(io, header=header):
        # Save the header chunk so that we can pass it to `read_chunk`
        # in the subsequent iterations. We use it internally to deserialize
        # the data chunk(s).
        if isinstance(chunk, (IhdrChunk, ShdrChunk)):
            header = chunk
        # Store all data chunks
        elif isinstance(chunk, (IdatChunk, SdatChunk)):
            data.append(chunk)
        elif isinstance(chunk, UnidentifiedAncilliaryChunk):
            # Discard all unidentified ancilliary (non-critical) chunks
            pass
        # We cover all chunk types, sd we should not hit this `else`
        else:
            assert False
    # The IQS file contained no header or data
    if header is None or not data:
        return None
    # Convert everything to the version 2.0.0 chunk types (IHDR and IDAT)
    ihdr = _ensure_ihdr(header, site_name=version_1_0_0_site_name)
    idats = (
        _ensure_idat(chunk, site_name=version_1_0_0_site_name, header=header)
        for chunk in data
    )
    # Merge all data together
    merged_idat = IdatChunk.merge_all(*idats, ihdr=ihdr)
    return IqsAggregate.from_chunks(ihdr, merged_idat)


def to_io(
    aggregate: IqsAggregate,
    io: BinaryIO,
    *,
    version: IqsVersion = IqsVersion.V2_0_0,
    site_to_keep: Optional[str] = None,
) -> None:
    """Serialize IQS aggregate to the IO stream.

    May raise:
      * `IqsError` or one of its derivatives.
      * `RuntimeError` if the platform doesn't natively support 4-byte integers.
    """
    write_signature(io)
    ihdr, idat = aggregate.to_chunks()
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
        raise IqsError("Need an SHDR chunk to convert an SDAT chunk to IDAT")
    return IdatChunk.from_sdat(
        chunk,
        site_name=site_name,
        time_step_ns=header.time_step_ns,
    )
