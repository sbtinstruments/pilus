from collections import defaultdict
from typing import Any, Iterable

from .._merge import MERGERS
from ._snip_part import SnipPart
from ._snip_part_metadata import SnipPartMetadata


def merge_snip_parts(parts: Iterable[SnipPart[Any]]) -> Iterable[SnipPart[Any]]:
    """Merge snip parts with the globally-registered mergers."""
    md: defaultdict[SnipPartMetadata, list[SnipPart[Any]]] = defaultdict(list)
    for part in parts:
        md[part.metadata].append(part)

    for metadata in set(md.keys()):
        matches = md[metadata]

        if len(matches) <= 1:
            yield from matches
            continue

        input_types = frozenset(type(part.value) for part in matches)
        try:
            merger = MERGERS[input_types]
        except KeyError:
            yield from matches
            continue

        values = (part.value for part in matches)
        merged_value = merger(*values)
        yield SnipPart(value=merged_value, metadata=metadata)
