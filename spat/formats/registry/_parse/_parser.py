from pathlib import Path
from typing import Any, BinaryIO, Protocol, Union


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


Parser = Union[DirParser, FileParser, IoParser, DataParser]
