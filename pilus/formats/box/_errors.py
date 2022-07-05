from .._errors import PilusError


class BoxError(PilusError):
    """Raised if we fail to deserialize the box format."""
