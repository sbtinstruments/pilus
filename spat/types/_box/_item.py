from dataclasses import dataclass


@dataclass(frozen=True)
class BoxItem:
    media_type: str
    data: bytes
