from typing import BinaryIO

from ._errors import IqsMissingDataError

IQS_BYTE_ORDER = "little"


def read_int(io: BinaryIO, size: int, signed: bool = False) -> int:
    """Read integer of the given byte size.

    May raise:
      * `OSError`
      * `IqsMissingDataError`
      * `ValueError` on invalid integers
    """
    return int.from_bytes(
        read_exactly(io, size), byteorder=IQS_BYTE_ORDER, signed=signed
    )


def read_fixed_string(io: BinaryIO, max_size: int, *, terminator: str = "\x00") -> str:
    """Read a fixed-length string.

    May raise:
      * `OSError`
      * `IqsMissingDataError`
      * `UnicodeDecodeError`
      * `ValueError` if there is no terminator in the string
    """
    full_str = read_exactly(io, max_size).decode()
    return full_str[: full_str.index(terminator)]


def read_exactly(io: BinaryIO, size: int) -> bytes:
    """Read `size` bytes from the binary IO stream.

    May raise:
      * `OSError`
      * `IqsMissingDataError` if we didn't read exactly `size` bytes.
    """
    data = io.read(size)
    number_of_bytes_read = len(data)
    if number_of_bytes_read != size:
        raise IqsMissingDataError(
            f"Expected {size} bytes but could only read {number_of_bytes_read} bytes",
            number_of_bytes_read=number_of_bytes_read,
        )
    return data

