from pathlib import Path
from typing import Any, BinaryIO

from ..._errors import SpatOSError
from ._deserializer import DataDeserializer, FileDeserializer, IoDeserializer


def generate_file_deserializer(io_deserializer: IoDeserializer) -> FileDeserializer:
    """Return auto-generated file deserializer from the given IO deserializer."""

    def _from_file(file: Path) -> Any:
        # Open file as IO stream
        try:
            io = file.open("rb")
        except OSError as exc:
            raise SpatOSError(f"Could not open file: {str(exc)}") from exc
        # Read and deserialize IO stream
        try:
            return io_deserializer(io)
        finally:
            io.close()

    return _from_file


def generate_io_deserializer(data_deserializer: DataDeserializer) -> IoDeserializer:
    """Return auto-generated IO deserializer from the given data deserializer.

    The generated deserializer simply reads all data into memory and forwards it to
    the data deserializer.
    """

    def _from_io(io: BinaryIO) -> Any:
        # Read everything into memory
        try:
            data = io.read()
        except OSError as exc:
            raise SpatOSError(f"Could not read file: {str(exc)}") from exc
        # Return deserialized data
        return data_deserializer(data)

    return _from_io
