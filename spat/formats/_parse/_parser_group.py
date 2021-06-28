from __future__ import annotations

from dataclasses import dataclass
from os import PathLike
from typing import Any, BinaryIO, Optional

from ._errors import SpatNoParserError
from ._generate_parser import generate_file_parser, generate_io_parser
from ._parser import DataParser, DirParser, FileParser, IoParser
from ._resource import IdentifiedResource


@dataclass(frozen=True)
class ParserGroup:
    """Group of parsers and utilities to auto-generate missing parsers."""

    from_dir: Optional[DirParser] = None
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
        """Return file parser (generate the parser if it's missing)."""
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
        """Return IO parser (generate the parser if it's missing)."""
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
        #
        # Note that we use `PathLike` and not `Path` so that alternative paths
        # also work. E.g., pyfakefs paths.
        if isinstance(identified.resource, PathLike):
            # Directory
            if identified.resource.is_dir():
                if self.from_dir is None:
                    raise SpatNoParserError(
                        "No registered directory parser found for media "
                        f'type "{identified.media_type}"'
                    )
                return self.from_dir(identified.resource)
            # File
            if identified.resource.is_file():
                from_file = self.auto_from_file()
                return from_file(identified.resource)
            # Other
            raise ValueError("Path resource does not point to a directory or file")
        # Resource is an IO stream. We use `from_io` to parse it. We auto-generate
        # `from_io` if it's missing.
        if isinstance(identified.resource, BinaryIO):
            from_io = self.auto_from_io()
            return from_io(identified.resource)
        # Resource is in-memory data. We use `from_data` to parse it.
        if isinstance(identified.resource, bytes):
            if self.from_data is None:
                raise SpatNoParserError(
                    "No registered data parser found for media "
                    f'type "{identified.media_type}"'
                )
            return self.from_data(identified.resource)
        assert False
