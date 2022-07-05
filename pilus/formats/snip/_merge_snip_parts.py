from collections import defaultdict
from typing import Any, Iterable

from ..registry import get_merger
from ._snip_part import SnipPart
from ._snip_part_metadata import SnipPartMetadata

_MultiDict = defaultdict[SnipPartMetadata, list[SnipPart[Any]]]


def merge_snip_parts(parts: Iterable[SnipPart[Any]]) -> Iterable[SnipPart[Any]]:
    """Merge snip parts with the globally-registered mergers.

    Parts with identical metadata is up for merge.
    If all parts have unique metadata, this function does nothing.
    """
    # Index each part by it's metadata in `part_lists`. This way, parts with identical
    # metadata ends up in the same list.
    part_lists: _MultiDict = defaultdict(list)
    for part in parts:
        part_lists[part.metadata].append(part)
    # Go through each part list and see if we can merge the parts in the list
    for metadata, part_list in part_lists.items():
        # If there is only a single item in the list, this means that the part doesn't
        # share metadata with another part. We simply yield the part as-is.
        if len(part_list) <= 1:
            yield from part_list
            continue
        # We merge parts based on their type. See if we can find a compatible merger.
        part_types = frozenset(type(part.value) for part in part_list)
        merger = get_merger(part_types)
        if merger is None:
            # There is no compatible merger. Simply yield the parts as-is.
            yield from part_list
            continue
        # Merge the parts' values and yield the result
        values = (part.value for part in part_list)
        merged_value = merger(*values)
        yield SnipPart(value=merged_value, metadata=metadata)
