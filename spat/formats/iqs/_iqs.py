from dataclasses import dataclass
from enum import Enum, auto
from typing import BinaryIO, Optional

from ._chunks import IdatChunk, IhdrChunk, SdatChunk, ShdrChunk, read_chunk, write_chunk
from ._signature import read_and_validate_signature, write_signature


class IqsVersion(Enum):
    """Version of the IQS specification."""

    V1_0_0 = auto()
    V2_0_0 = auto()


@dataclass(frozen=True)
class Iqs:
    """Raw IQS chunks."""

    ihdr: IhdrChunk
    idat: IdatChunk


def from_io(io: BinaryIO) -> Optional[Iqs]:
    """Deserialize IO stream into an IQS instance.

    Supports version 2 of the IQS specification.

    May raise `IqsError` or one of its derivatives.

    Merges all IDAT chunks into a single IDAT chunk. This way, all the raw binary
    data is contiguous.
    """
    read_and_validate_signature(io)
    ihdr: Optional[IhdrChunk] = None
    idats: list[IdatChunk] = list()
    while chunk := read_chunk(io, ihdr=ihdr):
        # Save the IHDR chunk so that we can pass it to `read_chunk`
        # in the subsequent iterations. We use it internally to deserialize
        # the IDAT chunk(s).
        if isinstance(chunk, IhdrChunk):
            ihdr = chunk
        # Store all data chunks
        elif isinstance(chunk, IdatChunk):
            idats.append(chunk)
    # The IQS file contained no data
    if ihdr is None or not idats:
        return None
    # Merge all data together
    merged_idat = IdatChunk.merge_all(*idats, ihdr=ihdr)
    return Iqs(ihdr, merged_idat)


def to_io(
    iqs: Iqs,
    io: BinaryIO,
    *,
    version: IqsVersion = IqsVersion.V2_0_0,
    site_to_keep: Optional[str] = None,
) -> None:
    """Serialize IQS instance to the IO stream.

    May raise:
      * `IqsError` or one of its derivatives.
      * `RuntimeError` if the platform doesn't natively support 4-byte integers.
    """
    write_signature(io)
    if version is IqsVersion.V2_0_0:
        write_chunk(io, iqs.ihdr)
        write_chunk(io, iqs.idat)
    elif version is IqsVersion.V1_0_0:
        if site_to_keep is None:
            raise ValueError(
                "You must specify `site_to_keep` when you target "
                "version 1.0.0 of the IQS specification."
            )
        write_chunk(io, ShdrChunk.from_ihdr(iqs.ihdr, site_to_keep=site_to_keep))
        write_chunk(io, SdatChunk.from_idat(iqs.idat, site_to_keep=site_to_keep))
    else:
        assert False
