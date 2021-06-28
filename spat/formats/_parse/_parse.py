from pathlib import Path
from typing import Any, BinaryIO, Optional, Union

from ._errors import SpatNoParserError
from ._parser import DataParser, DirParser, FileParser, IoParser
from ._parser_group import ParserGroup
from ._resource import IdentifiedResource

# Global dict of all registered parsers
_MEDIA_TYPE_TO_PARSER_GROUP: dict[str, ParserGroup] = dict()


def register_parsers(
    media_type: str,
    *,
    from_dir: Optional[DirParser] = None,
    from_file: Optional[FileParser] = None,
    from_io: Optional[IoParser] = None,
    from_data: Optional[DataParser] = None,
) -> None:
    """Use the parsers for the given media type."""
    group = ParserGroup(from_dir, from_file, from_io, from_data)
    register_parser_group(media_type, group)


def register_parser_group(media_type: str, group: ParserGroup) -> None:
    """Use the parser group for the given media type."""
    if group.is_empty():
        raise ValueError("You must specify at least one parser")
    # If there is no existing group, we simply assign the given group
    try:
        existing_group = _MEDIA_TYPE_TO_PARSER_GROUP[media_type]
    except KeyError:
        _MEDIA_TYPE_TO_PARSER_GROUP[media_type] = group
        return
    # Otherwise, we attempt to merge the two groups and use the result
    _MEDIA_TYPE_TO_PARSER_GROUP[media_type] = existing_group.merge(group)


def parse(media_type: str, resource: Union[Path, BinaryIO, bytes]) -> Any:
    """Parse the resource according to the media type."""
    identified = IdentifiedResource(media_type, resource)
    return parse_identified(identified)


def parse_identified(identified: IdentifiedResource) -> Any:
    """Parse the given identified resource (known media type)."""
    try:
        group = _MEDIA_TYPE_TO_PARSER_GROUP[identified.media_type]
    except KeyError as exc:
        raise SpatNoParserError(
            f'No parser found for media type: "{identified.media_type}"'
        ) from exc
    return group.parse(identified)
