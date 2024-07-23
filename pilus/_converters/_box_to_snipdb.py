from typing import Any, Iterable

from ..basic import Box
from ..errors import PilusConversionError
from ..forge import FORGE, Morpher
from ..snipdb import SnipAttrDeclMap, SnipDb, SnipRow, SnipRowMetadata


def box_to_snipdb(box: Box) -> SnipDb:
    """Convert box to snip DB."""
    box_parts = dict(box.items())

    try:
        attr_decls = box_parts.pop("attributes.json")
    except KeyError as exc:
        raise PilusConversionError('Could not find the "attributes.json" file') from exc
    attr_decls = FORGE.deserialize(attr_decls, SnipAttrDeclMap)

    try:
        data = box_parts.pop("data")
    except KeyError as exc:
        raise PilusConversionError('Could not find the "data" directory') from exc
    # `Box` is an `immutables.Map` which mypy has some troubles with.
    if not isinstance(data, Box):  # type: ignore[misc]
        raise PilusConversionError('The "data" entry is not a directory')

    snip_rows = _resolve_rows(data, attr_decls=attr_decls)

    # Raise an error if there are unexpected parts
    if box_parts:
        key = next(iter(box_parts))
        raise PilusConversionError(f'Unexpected entry "{key}"')

    return SnipDb(snip_rows, attr_decls)


def _resolve_rows(box: Box, *, attr_decls: SnipAttrDeclMap) -> Iterable[SnipRow[Any]]:
    for key, box_item in box.items():
        # `Box` is an `immutables.Map` which mypy has some troubles with.
        if isinstance(box_item, Box):  # type: ignore[misc]
            raise PilusConversionError(
                f'Unexpected sub-directory inside the data directory: "{key}"'
            )
        metadata = SnipRowMetadata.from_file_name(key, attr_decls=attr_decls)
        yield SnipRow(content=box_item, metadata=metadata)


FORGE.add_morpher(
    Morpher(
        input=Box,
        output=SnipDb,
        func=box_to_snipdb,
    )
)
