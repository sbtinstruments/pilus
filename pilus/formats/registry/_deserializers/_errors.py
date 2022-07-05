from ..._errors import PilusError


class PilusMissingDeserializerError(PilusError):
    """Raised when we can't find a deserializer for a given media type."""
