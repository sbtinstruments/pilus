from os import SEEK_CUR
from typing import BinaryIO

from ._errors import IqsError, IqsMissingDataError, IqsOSError, IqsUnicodeDecodeError

IQS_BYTE_ORDER = "little"


def read_int(io: BinaryIO, size: int, signed: bool = False) -> int:
    """Read integer of the given byte size.

    May raise `IqsError` or one of its derivatives. Specifically:
      * `IqsOSError`
      * `IqsMissingDataError`
      * `IqsError` on invalid integers
    """
    data = read_exactly(io, size)
    try:
        return int.from_bytes(data, byteorder=IQS_BYTE_ORDER, signed=signed)
    except ValueError as exc:
        raise IqsError("Could not decode integer") from exc


def read_terminated_string(
    io: BinaryIO,
    max_size: int,
    *,
    terminator: str = "\x00",
) -> str:
    """Read a terminated string.

    May raise `IqsError` or one of its derivatives. Specifically:
      * `IqsOSError`
      * `IqsMissingDataError`
      * `IqsUnicodeDecodeError`
      * `IqsError` if there is no terminator in the string
    """
    full_str = read_string(io, max_size)
    try:
        terminator_pos = full_str.index(terminator)
    except ValueError as exc:
        raise IqsError("Could not find terminator in fixed-length string") from exc
    return full_str[:terminator_pos]


def read_string(io: BinaryIO, size: int) -> str:
    """Read a fixed-length string.

    May raise `IqsError` or one of its derivatives. Specifically:
      * `IqsOSError`
      * `IqsMissingDataError`
      * `IqsUnicodeDecodeError`
    """
    data = read_exactly(io, size)
    try:
        return data.decode()
    except UnicodeDecodeError as exc:
        raise IqsUnicodeDecodeError(*exc.args) from exc


def read_exactly(io: BinaryIO, size: int) -> bytes:
    """Read `size` bytes from the binary IO stream.

    May raise `IqsError` or one of its derivatives. Specifically:
      * `IqsOSError` on OS-level errors.
      * `IqsMissingDataError` if we didn't read exactly `size` bytes
    """
    try:
        data = io.read(size)
    except OSError as exc:
        raise IqsOSError(*exc.args) from exc
    number_of_bytes_read = len(data)
    if number_of_bytes_read != size:
        raise IqsMissingDataError(
            f"Expected {size} bytes but could only read {number_of_bytes_read} bytes",
            number_of_bytes_read=number_of_bytes_read,
        )
    return data


def skip_data(io: BinaryIO, size: int) -> None:
    """Skip `size` bytes of data in the IO stream.

    May raise `IqsError` or one of its derivatives. Specifically:
      * `IqsOSError` on OS-level errors
    """
    try:
        io.seek(size, SEEK_CUR)
    except OSError as exc:
        raise IqsOSError(*exc.args) from exc
