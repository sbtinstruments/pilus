from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Optional, Protocol, Union

from .._errors import SpatError, SpatOSError
from ._identified_data import (
    IdentifiedData,
    IdentifiedIo,
    IdentifiedPath,
    IdentifiedResource,
)


class SpatNoParserError(SpatError):
    """Raised when we can't find a parser for a given media type."""


class DirParser(Protocol):  # pylint: disable=too-few-public-methods
    """Callable that parses a directory and returns a corresponding object."""

    def __call__(self, __root: Path) -> Any:  # noqa: D102
        ...


class FileParser(Protocol):  # pylint: disable=too-few-public-methods
    """Callable that parses a file and returns a corresponding object."""

    def __call__(self, __file: Path) -> Any:  # noqa: D102
        ...


class DataParser(Protocol):  # pylint: disable=too-few-public-methods
    """Callable that parses binary data and returns a corresponding object."""

    def __call__(self, __data: bytes) -> Any:  # noqa: D102
        ...


class IoParser(Protocol):  # pylint: disable=too-few-public-methods
    """Callable that parses an IO stream and returns a corresponding object."""

    def __call__(self, __io: BinaryIO) -> Any:  # noqa: D102
        ...


Parser = Union[DataParser, IoParser, DataParser]


def generate_file_parser(io_parser: IoParser) -> FileParser:
    """Return auto-generated file parser from the given IO parser."""

    def _from_file(file: Path) -> Any:
        # Open file as IO stream
        try:
            io = file.open("rb")
        except OSError as exc:
            raise SpatOSError(f"Could not open file: {str(exc)}") from exc
        # Read and parse IO stream
        try:
            return io_parser(io)
        finally:
            io.close()

    return _from_file


def generate_io_parser(data_parser: DataParser) -> IoParser:
    """Return auto-generated IO parser from the given data parser.

    The generated parser simply reads all data into memory and forwards it to
    the data parser.
    """

    def _from_io(io: BinaryIO) -> Any:
        # Read everything into memory
        try:
            data = io.read()
        except OSError as exc:
            raise SpatOSError(f"Could not read file: {str(exc)}") from exc
        # Return parsed data
        return data_parser(data)

    return _from_io


@dataclass(frozen=True)
class ParserGroup:
    """Group of parsers and utilities to auto-generate missing parsers."""

    from_dir: Optional[FileParser] = None
    from_file: Optional[FileParser] = None
    from_io: Optional[IoParser] = None
    from_data: Optional[DataParser] = None

    def is_empty(self) -> bool:
        """Are there no parsers in this group."""
        return (
            self.from_dir is None
            and self.from_file is None
            and self.from_io is None
            and self.from_data is None
        )

    def merge(self, other: ParserGroup) -> ParserGroup:
        """Merge this with other.

        Raises `ValueError` on conflict.
        """
        if self.from_dir is not None and other.from_dir is not None:
            raise ValueError("There already is a directory parser in this group")
        if self.from_file is not None and other.from_file is not None:
            raise ValueError("There already is a file parser in this group")
        if self.from_io is not None and other.from_io is not None:
            raise ValueError("There already is an IO parser in this group")
        if self.from_data is not None and other.from_data is not None:
            raise ValueError("There already is a data parser in this group")
        from_dir = self.from_dir if self.from_dir is not None else other.from_dir
        from_file = self.from_file if self.from_file is not None else other.from_file
        from_io = self.from_io if self.from_io is not None else other.from_io
        from_data = self.from_data if self.from_data is not None else other.from_data
        return ParserGroup(from_dir, from_file, from_io, from_data)

    def auto_from_file(self) -> FileParser:
        """Generate and return a file parser if it is missing."""
        if self.from_file is not None:
            return self.from_file
        try:
            from_io = self.auto_from_io()
        except SpatNoParserError as exc:
            raise SpatNoParserError(
                "Can't generate file parser without an IO parser"
            ) from exc
        return generate_file_parser(from_io)

    def auto_from_io(self) -> IoParser:
        """Generate and return an IO parser if it is missing."""
        if self.from_io is not None:
            return self.from_io
        if self.from_data is None:  # [1]
            raise SpatNoParserError("Can't generate IO parser without a data parser")
        return generate_io_parser(self.from_data)

    def parse(self, identified: IdentifiedResource) -> Any:
        """Parse the given resource.

        We prioritize the parsers as follows (highest priority first):

          1. `from_dir` and `from_file`
          2. `from_io`
          3. `from_data`

        Note that both `from_dir`, `from_file` and `from_io` can potentially skip
        unused data and thus avoid memory bloat. In contrast, `file_data` works
        on in-memory data so we already bloated the memory with potentially unused data.

        We auto-generate `from_file` and `from_io` if they are missing. Note that
        the auto auto-generated `from_io` simply call `from_data` and thus provide no
        potential memory savings. It's merely a convenience wrapper.
        """
        # Resource is a path. If the path points to a directory, we use `from_dir` to
        # parse it. If the path points to a file, we use `from_file` to parse it.
        # We auto-generate `from_file` if it's missing.
        if isinstance(identified, IdentifiedPath):
            # Directory
            if identified.path.is_dir():
                if self.from_dir is None:
                    raise SpatNoParserError(
                        "No registered directory parser found for media "
                        f'type "{identified.media_type}"'
                    )
                return self.from_dir(identified.path)
            # File
            if identified.path.is_file():
                from_file = self.auto_from_file()
                return from_file(identified.path)
            # Other
            raise ValueError("Path resource does not point to a directory or file")
        # Resource is an IO stream. We use `from_io` to parse it. We auto-generate
        # `from_io` if it's missing.
        if isinstance(identified, IdentifiedIo):
            from_io = self.auto_from_io()
            return from_io(identified.io)
        # Resource is in-memory data. We use `from_data` to parse it.
        if isinstance(identified, IdentifiedData):
            if self.from_data is None:
                raise SpatNoParserError(
                    "No registered data parser found for media "
                    f'type "{identified.media_type}"'
                )
            return self.from_data(identified.data)
        assert False


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


def parse(identified: IdentifiedResource) -> Any:
    """Parse the given resource and return the result."""
    try:
        group = _MEDIA_TYPE_TO_PARSER_GROUP[identified.media_type]
    except KeyError as exc:
        raise SpatNoParserError(
            f'No parser found for media type: "{identified.media_type}"'
        ) from exc
    return group.parse(identified)
