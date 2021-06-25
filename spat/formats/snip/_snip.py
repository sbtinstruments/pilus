from pathlib import Path
from typing import Dict

from immutables._map import Map

from ...types import Box, Snip, SnipKey, SnipValue
from .. import box as box_format
from .._utility import freeze_mapping
from ._attributes import Attributes
from ._errors import SnipError


def from_dir(root: Path) -> Snip:
    try:
        box = box_format.from_dir(root)
    except box_format.BoxError as exc:
        raise SnipError(f"Could not read box format: {str(exc)}") from exc
    return from_box(box)


def from_box(box: Box) -> Snip:
    items = dict(box.items())

    try:
        attributes = items.pop("attributes.json")
    except KeyError as exc:
        raise SnipError('Could not find the "attributes.json" file')
    if not isinstance(attributes, Attributes):
        raise SnipError('The "attributes.json" entry is not of the right type')

    try:
        data = items.pop("data")
    except KeyError as exc:
        raise SnipError('Could not find the "data" directory')
    if not isinstance(data, Box):
        raise SnipError('The "data" entry is not a directory')

    items = _resolve_data(data)

    if items:
        key = next(iter(items))
        raise SnipError(f'Unexpected entry "{key}"')

    return Snip(items)


def _resolve_data(box: Box) -> SnipValue:
    raw_items: Dict[str, SnipValue] = {}
    for key, box_item in box.items():
        snip_item: SnipValue
        if isinstance(box_item, Box):
            raise SnipError(
                f'Unexpected sub-directory inside the data directory: "{key}"'
            )
        snip_item = box_item
        snip_key = SnipKey.from_file_name(key)
        raw_items[snip_key] = snip_item
    return freeze_mapping(raw_items)
