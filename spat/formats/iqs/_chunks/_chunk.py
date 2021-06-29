from dataclasses import dataclass
from os import SEEK_CUR
from typing import BinaryIO, Optional, Union

from .._errors import IqsError, IqsMissingDataError
from .._io_utilities import read_exactly, read_int
from ._idat import IdatChunk, read_idat
from ._ihdr import IhdrChunk, read_ihdr


@dataclass(frozen=True)
class NonCriticalChunk:
    """Non-critical chunk."""


Chunk = Union[NonCriticalChunk, IhdrChunk, IdatChunk]


def read_chunk(io: BinaryIO, *, ihdr: Optional[IhdrChunk] = None) -> Optional[Chunk]:
    """Read IQS chunk.

    May raise `IqsError`.
    """
    # Early out if there is no more data in the IO stream
    chunk_length = _read_chunk_length(io)
    if chunk_length is None:
        return None
    try:
        # Read chunk type
        chunk_type = _read_chunk_type(io)
        # Read chunk data
        chunk = _read_chunk_data(io, chunk_type, chunk_length, ihdr=ihdr)
        # TODO: Implement CRC check
        # For now, we skip the CRC check
        io.seek(4, SEEK_CUR)
        return chunk
    except (OSError, IqsMissingDataError, ValueError, UnicodeDecodeError) as exc:
        raise IqsError(f'Could not deserialize chunk: "{exc}"') from exc


def _read_chunk_length(io: BinaryIO) -> Optional[int]:
    """Read chunk length.

    May raise `IqsError`.
    """
    try:
        return read_int(io, 4)
    except (OSError, ValueError) as exc:
        raise IqsError(f'Could not read chunk length: "{exc}"') from exc
    except IqsMissingDataError as exc:
        # There is no more data so return `None`
        if exc.number_of_bytes_read == 0:
            return None
        # There is some data but not enough to become a chunk length
        raise IqsError(f'Could not read chunk length: "{exc}"') from exc


def _read_chunk_type(io: BinaryIO) -> str:
    """Read the 4-byte chunk ID.

    May raise:
      * `OSError`
      * `IqsMissingDataError`
      * `UnicodeDecodeError` on invalid strings
    """
    return read_exactly(io, 4).decode()


def _read_chunk_data(
    io: BinaryIO,
    chunk_type: str,
    chunk_length: int,
    *,
    ihdr: Optional[IhdrChunk] = None,
) -> Chunk:
    """Read and parse chunk data of the given type and length.

    May raise:
      * `OSError`
      * `IqsMissingDataError`
      * `UnicodeDecodeError` on invalid strings
      * `ValueError` on invalid strings/integers
    """
    # TODO: Add support for the non-critical "sYSI" (system information) chunk
    # if chunk_type == "sYSI":
    #     return _read_sysi(io, chunk_length)
    if chunk_type == "IHDR":
        if ihdr is not None:
            raise IqsError("Encountered multiple IHDR chunks. There can only be one.")
        return read_ihdr(io)
    if chunk_type == "IDAT":
        if ihdr is None:
            raise IqsError("Encountered IDAT chunk before IHDR chunk.")
        return read_idat(io, ihdr=ihdr)
    # We don't reckognize the chunk type.
    # Check the so-called "ancilliary bit" to see if it's a critical chunk
    chunk_is_critical = chunk_type[0].isupper()
    if chunk_is_critical:
        # Raise an error if we can't deserialize a critical chunk
        raise IqsError(f'Encountered unknown critical chunk: "{chunk_type}"')
    # Skip non-critical chunks
    io.seek(chunk_length, SEEK_CUR)
    return NonCriticalChunk()


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
