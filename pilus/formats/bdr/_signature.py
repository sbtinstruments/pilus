from typing import BinaryIO

from ._errors import BdrError
from ..iqs._signature import read_signature
from ..iqs._io_utilities import write_exactly

_BDR_SIGNATURE = b"\x89BDR\x0D\x0A\x1A\x0A"


def read_and_validate_signature(io: BinaryIO) -> None:
    """Read and validate the BDR signature.

    May raise `BdrError` or one of its derivatives.
    """
    try:
        signature = read_signature(io)
    except BdrError as exc:
        # Wrap the `IqsError` with some additional context
        raise BdrError(f'Could not read Bdr signature: "{exc}"') from exc
    if signature != _BDR_SIGNATURE:
        raise BdrError("Invalid BDR signature")


def write_signature(io: BinaryIO) -> None:
    """Write IQS signature.

    May raise `IqsError` or one of its derivatives.
    """
    write_exactly(io, _BDR_SIGNATURE)