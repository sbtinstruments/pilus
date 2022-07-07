from typing import BinaryIO

from ...errors import PilusDeserializeError
from . import read_exactly, write_exactly


def read_and_validate_signature(io: BinaryIO, reference_signature: bytes) -> None:
    """Read and validate the given signature.

    May raise `PilusDeserializeError` or one of its derivatives.
    """
    try:
        signature = read_exactly(io, len(reference_signature))
    except PilusDeserializeError as exc:
        # Wrap the `PilusDeserializeError` with some additional context
        raise PilusDeserializeError(f'Could not read IQS signature: "{exc}"') from exc
    if signature != reference_signature:
        raise PilusDeserializeError("Invalid signature")


def write_signature(io: BinaryIO, signature: bytes) -> None:
    """Write the given signature.

    May raise `PilusSerializeError` or one of its derivatives.
    """
    write_exactly(io, signature)
