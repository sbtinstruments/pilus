from json import JSONDecodeError
from typing import Any

from pydantic import ValidationError


### General
class PilusBaseError(Exception):
    """Base class for all exceptions in the pilus package."""


class PilusOSError(PilusBaseError, OSError):
    """OS-level error in the pilus package."""


PilusValidationError = ValidationError


### ORM/database-like errors
class PilusNoResultFound(PilusBaseError):
    """Did not find any results."""


class PilusMultipleResultsFound(PilusBaseError):
    """Required a single result but found multiple."""


### Type conversions
class PilusConversionError(PilusBaseError):
    """Could not convert an instance from one type to another."""


class PilusMissingMorpherError(PilusConversionError):
    """Could not find a suitable morpher."""


### Serialization
class PilusSerializeError(PilusBaseError):
    """Could not serialize a medium."""


class PilusUnicodeEncodeError(PilusSerializeError, UnicodeEncodeError):
    """Could encode string in an pilus medium."""


### Deserialization
class PilusDeserializeError(PilusBaseError):
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


### Overall
# Any error that many come from pilus (or it's dependencies)
PilusError = PilusBaseError | PilusValidationError
