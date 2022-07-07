from json import JSONDecodeError
from typing import Any

from pydantic import ValidationError

### General


class PilusError(Exception):
    """Base class for all exceptions in the pilus package."""


class PilusOSError(PilusError, OSError):
    """OS-level error in the pilus package."""


class PilusValidationError(PilusError, ValidationError):
    """Error during validation.

    Note that `ValidationError` inherits from `ValueError`.
    """


### Type conversions
class PilusConversionError(PilusError):
    """Could not convert an instance from one type to another."""


class PilusMissingMorpherError(PilusConversionError):
    """Could not find a suitable morpher."""


### Serialization
class PilusSerializeError(PilusError):
    """Could not serialize a medium."""


class PilusUnicodeEncodeError(PilusSerializeError, UnicodeEncodeError):
    """Could encode string in an pilus medium."""


### Deserialization
class PilusDeserializeError(PilusError):
    """Could not deserialize a medium."""


class PilusJsonDecodeError(PilusDeserializeError, JSONDecodeError):
    """Error while we decode JSON in the pilus package."""


class PilusMissingDataError(PilusDeserializeError):
    """Could not read the expected amount of data."""

    def __init__(self, *args: Any, number_of_bytes_read: int) -> None:
        super().__init__(*args)
        self.number_of_bytes_read = number_of_bytes_read


class PilusUnicodeDecodeError(PilusDeserializeError, UnicodeDecodeError):
    """Could decode string in an pilus medium."""
