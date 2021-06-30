from dataclasses import dataclass
from typing import BinaryIO, Optional

from ._chunks import IdatChunk, IhdrChunk, read_chunk, write_chunk
from ._signature import read_and_validate_signature, write_signature


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


def to_io(iqs: Iqs, io: BinaryIO) -> None:
    """Serialize IQS instance to the IO stream.

    Supports version 2 of the IQS specification.

    May raise `IqsError` or one of its derivatives.
    """
    write_signature(io)
    write_chunk(io, iqs.ihdr)
    write_chunk(io, iqs.idat)
