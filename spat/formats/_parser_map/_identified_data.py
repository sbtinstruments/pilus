from dataclasses import dataclass


@dataclass(frozen=True)
class IdentifiedData:
    """Raw binary data identified by it's media type."""

    media_type: str
    data: bytes
