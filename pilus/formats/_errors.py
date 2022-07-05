from json import JSONDecodeError

from pydantic import ValidationError


class PilusError(Exception):
    """Base class for all exceptions in the pilus package."""


class PilusOSError(PilusError, OSError):
    """OS-level error in the pilus package."""


class PilusJsonDecodeError(PilusError, JSONDecodeError):
    """Error while we decode JSON in the pilus package."""


class PilusValidationError(PilusError, ValidationError):
    """Error during validation.

    Note that `ValidationError` inherits from `ValueError`.
    """
