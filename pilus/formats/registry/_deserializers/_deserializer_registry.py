from pathlib import Path
from typing import Any, BinaryIO, Optional, Union

from ._deserializer import (
    DataDeserializer,
    DirDeserializer,
    FileDeserializer,
    IoDeserializer,
)
from ._deserializer_group import DeserializerGroup
from ._errors import PilusMissingDeserializerError
from ._resource import IdentifiedResource

# Global dict of all registered deserializers
_DESERIALIZERS: dict[str, DeserializerGroup] = dict()


def add_deserializer(
    media_type: str,
    *,
    from_dir: Optional[DirDeserializer] = None,
    from_file: Optional[FileDeserializer] = None,
    from_io: Optional[IoDeserializer] = None,
    from_data: Optional[DataDeserializer] = None,
) -> None:
    """Add the given deserializers to the global registry.

    This associates the given media type with the deserializers. In other words,
    the `deserialize` function invokes the deserializer when it comes across the
    corresponding media type.
    """
    group = DeserializerGroup(from_dir, from_file, from_io, from_data)
    add_deserializer_group(media_type, group)


def add_deserializer_group(media_type: str, group: DeserializerGroup) -> None:
    """Add the given deserializer group to the global registry."""
    if group.is_empty():
        raise ValueError("You must specify at least one deserializer")
    # If there is no existing group, we simply assign the given group
    try:
        existing_group = _DESERIALIZERS[media_type]
    except KeyError:
        _DESERIALIZERS[media_type] = group
        return
    # Otherwise, we attempt to merge the two groups and use the result
    _DESERIALIZERS[media_type] = existing_group.merge(group)


def deserialize(media_type: str, resource: Union[Path, BinaryIO, bytes]) -> Any:
    """Deserializer the resource according to the media type."""
    identified = IdentifiedResource(media_type, resource)
    return deserialize_identified(identified)


def deserialize_identified(identified: IdentifiedResource) -> Any:
    """Deserializer the given identified resource (known media type)."""
    try:
        group = _DESERIALIZERS[identified.media_type]
    except KeyError as exc:
        raise PilusMissingDeserializerError(
            f'No deserializer found for media type: "{identified.media_type}"'
        ) from exc
    return group.deserialize(identified)
