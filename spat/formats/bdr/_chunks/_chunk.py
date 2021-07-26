from dataclasses import dataclass
from io import SEEK_CUR, BytesIO
from typing import BinaryIO, Optional, Union

from ._ahdr import AhdrChunk
from ._tran import TranChunk
from ._misc import OdatChunk, NoisChunk, ExtrChunk, PcexChunk, BlinChunk, RtraChunk

from .._errors import BdrError, BdrMissingDataError

from ...iqs._io_utilities import read_exactly, read_int, seek, write_exactly, write_int
from ...iqs._chunks._chunk import _chunk_crc
from ...iqs._errors import IqsMissingDataError


@dataclass(frozen=True)
class UnidentifiedAncilliaryChunk:
    """Non-critical chunk."""

DataChunk = Union[AhdrChunk, TranChunk]
NotImplementedChunk = Union[OdatChunk, NoisChunk, ExtrChunk, PcexChunk,
    BlinChunk, RtraChunk, UnidentifiedAncilliaryChunk]
Chunk = Union[DataChunk, NotImplementedChunk]


def read_chunk(io: BinaryIO, header: Optional[AhdrChunk] = None) -> Optional[Chunk]:
    """Read BDR chunk.

    May raise `BdrError` or one of its derivatives.
    """
    # Early out if there is no more data in the IO stream
    chunk_length = _read_chunk_length(io)
    if chunk_length is None:
        return None
    # Read chunk type
    chunk_type = read_exactly(io, 4)
    # Read chunk data
    chunk_data = read_exactly(io, chunk_length)
    chunk = _deserialize_chunk_data(chunk_type, chunk_data, header=header, length=chunk_length)
    # CRC check
    actual_crc = _chunk_crc(chunk_type, chunk_data)
    expected_crc = read_int(io, 4)
    if actual_crc != expected_crc:
        raise BdrError("CRC mismatch")
    return chunk


def _read_chunk_length(io: BinaryIO) -> Optional[int]:
    """Read chunk length.

    May raise `IqsError` or one of its derivatives.
    """
    try:
        return read_int(io, 4)
    except IqsMissingDataError as exc:
        # There is no more data so return `None`
        if exc.number_of_bytes_read == 0:
            return None
        # There is some data but not enough to become a chunk length
        raise BdrError(f'Could not read chunk length: "{exc}"') from exc
    except BdrError as exc:
        # Wrap the `BdrError` with some additional context
        raise BdrError(f'Could not read chunk length: "{exc}"') from exc


def _deserialize_chunk_data(
    chunk_type: bytes,
    chunk_data: bytes,
    header: Optional[AhdrChunk] = None,
    length: Optional[int] = None
) -> Chunk:
    """Read and parse chunk data of the given type and length.

    May raise `IqsError` or one of its derivatives.
    """
    # It may seem a bit strange that we convert `chunk_data` back into an IO
    # stream here. The reasoning is three-fold:
    #   1. We already read all the data into memory to compute the CRC. It doesn't
    #      make sense to read it again just to satisfy the `from_io` interface.
    #   2. The various deserializers only requires a single pass over the data. In
    #      other words, the deserializers only require a `BinaryIO` stream and not
    #      the full `bytes` interface.
    #   3. The deserializers require the notion of "position within the data" that
    #      you get from `BinaryIO` but not from `bytes`. if we only got `bytes`,
    #      we would have to keep track of this "position" anyway.
    chunk_data_io = BytesIO(chunk_data)
    # AHDR
    if chunk_type == AhdrChunk.type_:
        return AhdrChunk.from_io(chunk_data_io)
    # tRAN
    if (chunk_type == TranChunk.type_ 
        and header is not None
        and length is not None):
        return TranChunk.from_io(chunk_data_io, length, header=header)
    # All chunk types are in ASCII
    try:
        chunk_type_name = chunk_type.decode("ascii")
    except UnicodeDecodeError as exc:
        raise BdrError("Invalid chunk type") from exc
    # We don't recognize the chunk type.

    chunk_is_ancilliary = chunk_type_name[0].islower()
    if not chunk_is_ancilliary:
        # Raise an error if we can't deserialize a critical chunk
        raise BdrError(f'Encountered unknown critical chunk: "{chunk_type_name}"')
    return UnidentifiedAncilliaryChunk()