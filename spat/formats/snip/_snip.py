from pathlib import Path
from typing import Any, Dict, Iterable

from ...types import Box, Snip, SnipAttributeDeclaration, SnipPart, SnipPartMetadata
from .. import box as box_format
from ._errors import SnipError


def from_dir(root: Path) -> Snip:
    try:
        box = box_format.from_dir(root)
    except box_format.BoxError as exc:
        raise SnipError(f"Could not read box format: {str(exc)}") from exc
    return from_box(box)


def from_box(box: Box) -> Snip:
    box_parts = dict(box.items())

    try:
        attribute_declaration = box_parts.pop("attributes.json")
    except KeyError as exc:
        raise SnipError('Could not find the "attributes.json" file') from exc
    if not isinstance(attribute_declaration, SnipAttributeDeclaration):
        raise SnipError('The "attributes.json" entry is not of the right type')

    try:
        data = box_parts.pop("data")
    except KeyError as exc:
        raise SnipError('Could not find the "data" directory') from exc
    if not isinstance(data, Box):
        raise SnipError('The "data" entry is not a directory')

    snip_parts = _resolve_parts(data, attribute_declaration=attribute_declaration)

    # Raise an error if there are unexpected parts
    if box_parts:
        key = next(iter(box_parts))
        raise SnipError(f'Unexpected entry "{key}"')

    return Snip(snip_parts, attribute_declaration)


def _resolve_parts(
    box: Box, *, attribute_declaration: SnipAttributeDeclaration
) -> Iterable[SnipPart[Any]]:
    for key, box_item in box.items():
        if isinstance(box_item, Box):
            raise SnipError(
                f'Unexpected sub-directory inside the data directory: "{key}"'
            )
        metadata = SnipPartMetadata.from_file_name(
            key, attribute_declaration=attribute_declaration
        )
        yield SnipPart(
            name=metadata.name, attributes=metadata.attributes, value=box_item
        )
