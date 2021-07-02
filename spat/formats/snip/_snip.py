from pathlib import Path
from typing import Any, Iterable, Protocol, Type, TypeVar

from .. import box as box_format
from ..box import Box
from ._errors import SnipError
from ._merge_snip_parts import merge_snip_parts
from ._snip_attribute_declaration_map import SnipAttrDeclMap
from ._snip_part import SnipPart
from ._snip_part_metadata import SnipPartMetadata


class _InitProtocol(Protocol):  # pylint: disable=too-few-public-methods
    def __init__(  # pylint: disable=super-init-not-called
        self,
        __parts: Iterable[SnipPart[Any]],
        __attr_decls: SnipAttrDeclMap,
    ) -> None:
        ...


T = TypeVar("T", bound=_InitProtocol)


def from_dir(type_: Type[T], root: Path) -> T:
    """Parse directory into an instance of the given type."""
    try:
        box = box_format.from_dir(root)
    except box_format.BoxError as exc:
        raise SnipError(f"Could not read box format: {str(exc)}") from exc
    return from_box(type_, box)


def from_box(type_: Type[T], box: Box) -> T:
    """Parse box into an instance of the given type."""
    box_parts = dict(box.items())

    try:
        attr_decls = box_parts.pop("attributes.json")
    except KeyError as exc:
        raise SnipError('Could not find the "attributes.json" file') from exc
    if not isinstance(attr_decls, SnipAttrDeclMap):
        raise SnipError('The "attributes.json" entry is not of the right type')

    try:
        data = box_parts.pop("data")
    except KeyError as exc:
        raise SnipError('Could not find the "data" directory') from exc
    # `Box` is an `immutables.Map` which mypy has some troubles with.
    if not isinstance(data, Box):  # type: ignore[misc]
        raise SnipError('The "data" entry is not a directory')

    snip_parts = _resolve_parts(data, attr_decls=attr_decls)

    # Raise an error if there are unexpected parts
    if box_parts:
        key = next(iter(box_parts))
        raise SnipError(f'Unexpected entry "{key}"')

    # Merge parts
    nerged_parts = merge_snip_parts(snip_parts)

    return type_(nerged_parts, attr_decls)


def _resolve_parts(box: Box, *, attr_decls: SnipAttrDeclMap) -> Iterable[SnipPart[Any]]:
    for key, box_item in box.items():
        # `Box` is an `immutables.Map` which mypy has some troubles with.
        if isinstance(box_item, Box):  # type: ignore[misc]
            raise SnipError(
                f'Unexpected sub-directory inside the data directory: "{key}"'
            )
        metadata = SnipPartMetadata.from_file_name(key, attr_decls=attr_decls)
        yield SnipPart(value=box_item, metadata=metadata)
