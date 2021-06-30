from typing import Any

from .._errors import SpatError


class IqsError(SpatError):
    """Could not serialize/deserialize an IQS resource."""


class IqsMissingDataError(IqsError):
    """Could not read the expected amount of data."""

    def __init__(self, *args: Any, number_of_bytes_read: int) -> None:
        super().__init__(*args)
        self.number_of_bytes_read = number_of_bytes_read


class IqsOSError(IqsError, OSError):
    """OS-level error in the IQS package."""


class IqsUnicodeDecodeError(IqsError, UnicodeDecodeError):
    """Could decode string in an IQS resource."""


class IqsUnicodeEncodeError(IqsError, UnicodeEncodeError):
    """Could encode string in an IQS resource."""
