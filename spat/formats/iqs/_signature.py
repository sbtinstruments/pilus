from typing import BinaryIO

from ._errors import IqsError, IqsMissingDataError
from ._io_utilities import read_exactly

_IQS_SIGNATURE = b"\x89IQS\x0D\x0A\x1A\x0A"


def read_and_validate_signature(io: BinaryIO) -> None:
    """Read and validate the IQS signature.

    May raise `IqsError`.
    """
    try:
        signature = read_signature(io)
    except (OSError, IqsMissingDataError) as exc:
        raise IqsError(f'Could not read IQS signature: "{exc}"') from exc
    if signature != _IQS_SIGNATURE:
        raise IqsError("Invalid IQS signature")


def read_signature(io: BinaryIO) -> bytes:
    """Read IQS signature.

    May raise:
      * `OSError`
      * `IqsMissingDataError`
    """
    return read_exactly(io, 8)


# def _write_signature(io: BinaryIO, sign="894951530d0a1a0a"):
#     """Write IQS signature."""
#     return io.write(bytes.fromhex(sign))
