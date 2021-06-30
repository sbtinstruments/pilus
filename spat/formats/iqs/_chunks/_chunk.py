from dataclasses import dataclass
from io import SEEK_CUR, BufferedWriter, BytesIO
from typing import BinaryIO, Optional, Union

from .._crc import crc32
from .._errors import IqsError, IqsMissingDataError
from .._io_utilities import read_exactly, read_int, seek, write_exactly, write_int
from ._idat import IdatChunk
from ._ihdr import IhdrChunk


@dataclass(frozen=True)
class NonCriticalChunk:
    """Non-critical chunk."""


Chunk = Union[NonCriticalChunk, IhdrChunk, IdatChunk]


def read_chunk(io: BinaryIO, *, ihdr: Optional[IhdrChunk] = None) -> Optional[Chunk]:
    """Read IQS chunk.

    May raise `IqsError` or one of its derivatives.
    """
    # Early out if there is no more data in the IO stream
    chunk_length = _read_chunk_length(io)
    if chunk_length is None:
        return None
    # Read chunk type
    chunk_type = read_exactly(io, 4)
    # Read chunk data
    chunk_data = read_exactly(io, chunk_length)
    chunk = _deserialize_chunk_data(chunk_type, chunk_data, ihdr=ihdr)
    # CRC check
    actual_crc = _chunk_crc(chunk_type, chunk_data)
    expected_crc = read_int(io, 4)
    if actual_crc != expected_crc:
        raise IqsError("CRC mismatch")
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
        raise IqsError(f'Could not read chunk length: "{exc}"') from exc
    except IqsError as exc:
        # Wrap the `IqsError` with some additional context
        raise IqsError(f'Could not read chunk length: "{exc}"') from exc


def _deserialize_chunk_data(
    chunk_type: bytes,
    chunk_data: bytes,
    *,
    ihdr: Optional[IhdrChunk] = None,
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
    # TODO: Add support for the non-critical "sYSI" (system information) chunk
    # if chunk_type == "sYSI":
    #     return _read_sysi(io, chunk_length)
    if chunk_type == IhdrChunk.type_:
        if ihdr is not None:
            raise IqsError("Encountered multiple IHDR chunks. There can only be one.")
        return IhdrChunk.from_io(chunk_data_io)
    if chunk_type == IdatChunk.type_:
        if ihdr is None:
            raise IqsError("Encountered IDAT chunk before IHDR chunk.")
        return IdatChunk.from_io(chunk_data_io, ihdr=ihdr)
    # We don't reckognize the chunk type.
    # Check the so-called "ancilliary bit" to see if it's an:
    #   1. Ancilliary chunk (optional)
    #   2. Critical chunk (required)
    chunk_is_ancilliary = bool(chunk_type[0] & 0b10000)
    if not chunk_is_ancilliary:
        # Raise an error if we can't deserialize a critical chunk
        raise IqsError("Encountered unknown critical chunk")
    return NonCriticalChunk()


def write_chunk(io: BinaryIO, chunk: Union[IhdrChunk, IdatChunk]) -> None:
    """Serialize chunk into the IO stream.

    May raise `IqsError` or one of its derivatives.
    """
    # Serialize the chunk data itself
    chunk_data_io = BytesIO()
    # We know the data length up front so we can reserve (pre-allocate)
    # memory for it.
    chunk_data_length = chunk.data_length()
    _reserve(chunk_data_io, chunk_data_length)  # [1]
    chunk.to_io(chunk_data_io)
    # Our `chunk.data_length` function is exact. We neither reserve too much
    # or too little data at [1].
    assert chunk_data_length == len(chunk_data_io.getbuffer())
    # Write chunk length and type
    write_int(io, len(chunk_data_io.getbuffer()), 4)
    write_exactly(io, chunk.type_)
    # Then the data itself
    write_exactly(io, chunk_data_io.getbuffer())
    # Finally, write the CRC checksum of the data and type
    crc = _chunk_crc(chunk.type_, chunk_data_io.getbuffer())
    write_int(io, crc, 4)


def _reserve(io: BinaryIO, size: int) -> None:
    """Pre-allocate data in the IO stream."""
    if size < 0:
        raise IqsError("Can't reserve a negative number of bytes")
    if size == 0:
        return
    # Theory of operation:
    #
    #   1. Seek ahead
    #   2. Write a single byte
    #   3. Seek back to where we start
    #
    # If we only do (1) and (3) alone, we only move a position but we won't
    # cause any data allocation. Because we also do (2), we force the
    # stream to allocate the data.
    if size != 1:
        seek(io, size - 1, SEEK_CUR)
    write_exactly(io, bytes(1))
    seek(io, -size, SEEK_CUR)


def _chunk_crc(chunk_type: bytes, chunk_data: bytes) -> int:
    crc = 0xFFFFFFFF
    crc = crc32(chunk_type, crc)
    crc = crc32(chunk_data, crc)
    return crc


# def _read_sysi(io: BinaryIO, chunk_length):
#     info = json.loads(io.read(chunk_length))  # python3.9: encoding arg removed
#     crc = read_uint32(io)  # TODO: move crc check into fnc decorator
#     return info


# def _write_sysi(io: BinaryIO, iqs: dict) -> None:
#     """Write system information."""
#     sys_info = bytes(json.dumps(iqs["sys_info"]).replace(" ", ""), "utf-8")
#     byte_length = len(sys_info)
#     write_uint32(io, byte_length)
#     io.write(b"sYSI")
#     io.write(sys_info)
#     # write crc
#     write_uint32(io, 0)
