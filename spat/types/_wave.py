from dataclasses import dataclass


@dataclass(frozen=True)
class Wave:
    data: bytes = bytes()
