from io import SEEK_CUR
from struct import unpack
from typing import BinaryIO, Literal

from ....errors import (
    PilusDeserializeError,
    PilusMissingDataError,
    PilusOSError,
    PilusSerializeError,
    PilusUnicodeDecodeError,
    PilusUnicodeEncodeError,
)

IQS_BYTE_ORDER: Literal["little"] = "little"


def read_int(io: BinaryIO, size: int, *, signed: bool = False) -> int:
    """Read integer of the given byte size.

    May raise:
      * `PilusBaseError`
        * `PilusOSError`
        * `PilusDeserializeError`
          * `PilusMissingDataError`
    """
    data = read_exactly(io, size)
    try:
        return int.from_bytes(data, byteorder=IQS_BYTE_ORDER, signed=signed)
    except ValueError as exc:
        raise PilusDeserializeError("Could not decode integer") from exc


def read_double(io: BinaryIO) -> float:
    """Read 8-byte floating-point number.

    May raise:
      * `PilusBaseError`
        * `PilusOSError`
        * `PilusDeserializeError`
          * `PilusMissingDataError`
    """
    data = read_exactly(io, 8)
    try:
        (value,) = unpack("d", data)
        assert isinstance(value, float)
        return value
    except ValueError as exc:
        raise PilusDeserializeError("Could not decode double") from exc


def read_terminated_string(
    io: BinaryIO,
    max_size: int,
    *,
    terminator: str = "\x00",
) -> str:
    """Read a terminated string.

    May raise:
      * `PilusBaseError`
        * `PilusOSError`
        * `PilusDeserializeError`
          * `PilusMissingDataError`
          * `PilusUnicodeDecodeError`
    """
    full_str = read_string(io, max_size)
    try:
        terminator_pos = full_str.index(terminator)
    except ValueError as exc:
        raise PilusDeserializeError(
            "Could not find terminator in fixed-length string"
        ) from exc
    return full_str[:terminator_pos]


def read_string(io: BinaryIO, size: int) -> str:
    """Read a fixed-length string.

    May raise:
      * `PilusBaseError`
        * `PilusOSError`
        * `PilusDeserializeError`
          * `PilusMissingDataError`
          * `PilusUnicodeDecodeError`
    """
    data = read_exactly(io, size)
    try:
        return data.decode()
    except UnicodeDecodeError as exc:
        raise PilusUnicodeDecodeError(*exc.args) from exc


def read_exactly(io: BinaryIO, size: int) -> bytes:
    """Read `size` bytes from the binary IO stream.

    May raise:
      * `PilusBaseError`
        * `PilusOSError`
        * `PilusDeserializeError`
          * `PilusMissingDataError` (if we didn't read exactly `size` bytes)
    """
    try:
        data = io.read(size)
    except OSError as exc:
        raise PilusOSError(*exc.args) from exc
    number_of_bytes_read = len(data)
    if number_of_bytes_read != size:
        raise PilusMissingDataError(
            f"Expected {size} bytes but could only read {number_of_bytes_read} bytes",
            number_of_bytes_read=number_of_bytes_read,
        )
    return data


def seek(io: BinaryIO, size: int, whence: int) -> None:
    """Skip `size` bytes of data in the IO stream.

    May raise:
      * `PilusBaseError`
        * `PilusOSError`
    """
    try:
        io.seek(size, whence)
    except OSError as exc:
        raise PilusOSError(*exc.args) from exc


def tell(io: BinaryIO) -> int:
    """Return the current position in the IO stream.

    May raise:
      * `PilusBaseError`
        * `PilusOSError`
    """
    try:
        return io.tell()
    except OSError as exc:
        raise PilusOSError(*exc.args) from exc


def write_int(io: BinaryIO, value: int, size: int, *, signed: bool = False) -> None:
    """Encode integer and write the data to the IO stream.

    May raise:
      * `PilusBaseError`
        * `PilusOSError`
        * `PilusSerializeError`
    """
    try:
        data = value.to_bytes(size, byteorder=IQS_BYTE_ORDER, signed=signed)
    except ValueError as exc:
        raise PilusSerializeError(f'Could not encode integer: "{exc}"') from exc
    write_exactly(io, data)


def write_terminated_string(
    io: BinaryIO,
    value: str,
    max_size: int,
    *,
    terminator: bytes = b"\x00",
) -> None:
    """Encode string and write the data to the IO stream.

    May raise:
      * `PilusBaseError`
        * `PilusOSError`
        * `PilusSerializeError`
          * `PilusUnicodeEncodeError`
    """
    try:
        string_data = value.encode()
    except UnicodeEncodeError as exc:
        raise PilusUnicodeEncodeError(*exc.args) from exc
    data = string_data + terminator
    if len(data) > max_size:
        raise PilusSerializeError("Could not fit string into the given size.")
    write_exactly(io, data)
    remainder = max_size - len(data)
    seek(io, remainder, SEEK_CUR)


def write_exactly(io: BinaryIO, data: bytes) -> None:
    """Write binary data to the IO stream.

    May raise:
      * `PilusBaseError`
        * `PilusOSError`
        * `PilusSerializeError` (if we can't write all of the given data)
    """
    try:
        number_of_bytes_written = io.write(data)
    except OSError as exc:
        raise PilusOSError(*exc.args) from exc
    size = len(data)
    if number_of_bytes_written != size:
        raise PilusSerializeError(
            f"Could only write {number_of_bytes_written} bytes "
            f"of the total {size} bytes"
        )
