from json import JSONDecodeError

from pydantic import ValidationError


class SpatError(Exception):
    pass


class SpatOSError(SpatError, OSError):
    pass


class SpatJsonDecodeError(SpatError, JSONDecodeError):
    pass


class SpatValidationError(SpatError, ValidationError):
    """Error during validation.

    Note that `ValidationError` inherits from `ValueError`.
    """
