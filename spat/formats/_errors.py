from json import JSONDecodeError

from pydantic import ValidationError


class SpatError(Exception):
    """Base class for all exceptions in the spat package."""


class SpatOSError(SpatError, OSError):
    """OS-level error in the spat package."""


class SpatJsonDecodeError(SpatError, JSONDecodeError):
    """Error while we decode JSON in the spat package."""


class SpatValidationError(SpatError, ValidationError):
    """Error during validation.

    Note that `ValidationError` inherits from `ValueError`.
    """
