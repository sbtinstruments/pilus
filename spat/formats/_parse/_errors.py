from .._errors import SpatError


class SpatNoParserError(SpatError):
    """Raised when we can't find a parser for a given media type."""
