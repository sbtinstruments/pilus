from dataclasses import dataclass
from datetime import timedelta
from typing import BinaryIO, Optional

from ._chunks import IdatChunk, IhdrChunk, read_chunk
from ._signature import read_and_validate_signature


@dataclass(frozen=True)
class Iqs:
    """Raw IQS chunks."""

    ihdr: IhdrChunk
    idat: IdatChunk


def from_io(io: BinaryIO) -> Optional[Iqs]:
    """Deserialize IO stream into an IQS instance.

    Supports version 2 of the IQS specification.

    May raise `IqsError`.

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


# def write_iqs(iqs, file_name: str) -> bool:
#     """Write v2.0 iqs file."""
#     with open(file_name, "w+b") as f:
#         _write_signature(f)
#         _write_sysi(f, iqs)
#         _write_ihdr(f, iqs)
#         _write_idat(f, iqs)

#     return True
