from pathlib import Path
from typing import Any, BinaryIO, Optional, Union

from ._errors import SpatNoParserError
from ._parser import DataParser, DirParser, FileParser, IoParser
from ._parser_group import ParserGroup
from ._resource import IdentifiedResource

# Global dict of all registered parsers
_PARSERS: dict[str, ParserGroup] = dict()


def add_parsers(
    media_type: str,
    *,
    from_dir: Optional[DirParser] = None,
    from_file: Optional[FileParser] = None,
    from_io: Optional[IoParser] = None,
    from_data: Optional[DataParser] = None,
) -> None:
    """Add the given parsers to the global registry.

    This associates the given media type with the parsers. In other words,
    the `parse` function invokes the parser when it comes across the corresponding
    media type.
    """
    group = ParserGroup(from_dir, from_file, from_io, from_data)
    add_parser_group(media_type, group)


def add_parser_group(media_type: str, group: ParserGroup) -> None:
    """Add the given parser group to the global registry."""
    if group.is_empty():
        raise ValueError("You must specify at least one parser")
    # If there is no existing group, we simply assign the given group
    try:
        existing_group = _PARSERS[media_type]
    except KeyError:
        _PARSERS[media_type] = group
        return
    # Otherwise, we attempt to merge the two groups and use the result
    _PARSERS[media_type] = existing_group.merge(group)


def parse(media_type: str, resource: Union[Path, BinaryIO, bytes]) -> Any:
    """Parse the resource according to the media type."""
    identified = IdentifiedResource(media_type, resource)
    return parse_identified(identified)


def parse_identified(identified: IdentifiedResource) -> Any:
    """Parse the given identified resource (known media type)."""
    try:
        group = _PARSERS[identified.media_type]
    except KeyError as exc:
        raise SpatNoParserError(
            f'No parser found for media type: "{identified.media_type}"'
        ) from exc
    return group.parse(identified)
