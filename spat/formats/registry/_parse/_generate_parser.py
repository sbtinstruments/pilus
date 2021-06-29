from pathlib import Path
from typing import Any, BinaryIO

from ..._errors import SpatOSError
from ._parser import DataParser, FileParser, IoParser


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
