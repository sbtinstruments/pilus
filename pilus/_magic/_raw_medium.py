from __future__ import annotations

from os import PathLike
from typing import Any, BinaryIO, Type, Union, get_args

# Note that `PathLike` only covers classes like `pathlib.Path` and not `str`.
# `PathLike` is anyting with an `__fspath__` method (which `str` doesn't have).
# Indirectly, we force the user to be explicit and use, e.g., `Path` instances
# for file system paths (and avoid raw strings)
RawMedium = Union[PathLike, BinaryIO, bytes]
RawMediumType = Union[Type[PathLike], Type[BinaryIO], Type[bytes]]


def is_raw_medium(value: Any) -> bool:
    return isinstance(value, get_args(RawMedium)) or is_binary_io_like(value)


def is_binary_io_like(value: Any) -> bool:
    # Obviously true for actual `BinaryIO` instances
    if isinstance(value, BinaryIO):
        return True
    # Stuff `pyfakefs.FakeFileWrapper` is close enough to actual `BinaryIO`
    # that we let it through here.
    try:
        # HACK: Note that we do not import `FakeFileWrapper` to save the import time.
        # Instead, we just check the class name. Simple and fast.
        if value.__class__.__name__ == "FakeFileWrapper":
            return True
    except AttributeError:
        pass
    return False
