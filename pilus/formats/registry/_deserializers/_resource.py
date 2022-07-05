from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Union

Resource = Union[Path, BinaryIO, bytes]


@dataclass(frozen=True)
class IdentifiedResource:
    """Resource (path, IO stream, data, etc.) identified by a media type."""

    # TODO: Validate the media type. E.g., does it contain a "/" or valid "+" suffix?
    media_type: str
    resource: Resource
