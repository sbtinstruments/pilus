from .._errors import SpatError


class BoxError(SpatError):
    """Raised if we fail to deserialize the box format."""
