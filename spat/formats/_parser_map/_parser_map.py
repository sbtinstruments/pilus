from typing import Any, Callable, Union

from ._identified_data import IdentifiedData

Parser = Callable[[Union[str, bytes]], Any]

# Global dict of all registered parsers
_MEDIA_TYPE_TO_PARSER: dict[str, Parser] = {}


def register_parser(media_type: str, parser: Parser) -> None:
    """Use the parser to parse data with the given media type.

    Raises `ValueError` on conflict.
    """
    if media_type in _MEDIA_TYPE_TO_PARSER:
        raise ValueError(f'There already is a parser for "{media_type}"')
    _MEDIA_TYPE_TO_PARSER[media_type] = parser


def try_parse(identified: IdentifiedData) -> Any:
    """Try to parse the given data and return the result.

    Returns the input data if we don't know the media type.
    """
    try:
        parser = _MEDIA_TYPE_TO_PARSER[identified.media_type]
    except KeyError:
        return identified
    else:
        return parser(identified.data)


# _EXT_TO_MEDIA_TYPE: Dict[str, str] = {
#     ".wav": "audio/vnd.wave",
#     ".wav-meta.json": "application/vnd.sbt.wav-meta+json",
#     ".extrema.json": "application/vnd.sbt.extrema+json",
#     ".transitions.json": "application/vnd.sbt.transitions+json",
#     ".alg.json": "application/vnd.sbt.alg+json",
# }
