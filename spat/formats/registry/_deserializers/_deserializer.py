from pathlib import Path
from typing import Any, BinaryIO, Protocol, Union


class DirDeserializer(Protocol):  # pylint: disable=too-few-public-methods
    """Callable that deserializes a directory and returns a corresponding object."""

    def __call__(self, __root: Path) -> Any:  # noqa: D102
        ...


class FileDeserializer(Protocol):  # pylint: disable=too-few-public-methods
    """Callable that deserializes a file and returns a corresponding object."""

    def __call__(self, __file: Path) -> Any:  # noqa: D102
        ...


class DataDeserializer(Protocol):  # pylint: disable=too-few-public-methods
    """Callable that deserializes binary data and returns a corresponding object."""

    def __call__(self, __data: bytes) -> Any:  # noqa: D102
        ...


class IoDeserializer(Protocol):  # pylint: disable=too-few-public-methods
    """Callable that deserializes an IO stream and returns a corresponding object."""

    def __call__(self, __io: BinaryIO) -> Any:  # noqa: D102
        ...


Deserializer = Union[
    DirDeserializer, FileDeserializer, IoDeserializer, DataDeserializer
]
