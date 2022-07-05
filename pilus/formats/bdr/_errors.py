from typing import Any

from .._errors import PilusError


class BdrError(PilusError):
    """Could not serialize/deserialize an Bdr resource."""


class BdrMissingDataError(BdrError):
    """Could not read the expected amount of data."""

    def __init__(self, *args: Any, number_of_bytes_read: int) -> None:
        super().__init__(*args)
        self.number_of_bytes_read = number_of_bytes_read


class BdrOSError(BdrError, OSError):
    """OS-level error in the Bdr package."""


class BdrUnicodeDecodeError(BdrError, UnicodeDecodeError):
    """Could decode string in an Bdr resource."""


class BdrUnicodeEncodeError(BdrError, UnicodeEncodeError):
    """Could encode string in an Bdr resource."""
