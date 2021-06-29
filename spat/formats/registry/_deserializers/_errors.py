from ..._errors import SpatError


class SpatMissingDeserializerError(SpatError):
    """Raised when we can't find a deserializer for a given media type."""
