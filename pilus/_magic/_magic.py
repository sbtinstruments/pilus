from contextlib import contextmanager
from io import BytesIO
from os import PathLike
from pathlib import Path
from typing import BinaryIO, Iterator, cast

import magic

from ._raw_medium import RawMedium, is_binary_io_like
from .signatures import BDR_SIGNATURE, IQS_SIGNATURE

_LIBMAGIC_TRANSLATIONS: dict[str, str] = {
    "audio/x-wav": "audio/vnd.wave",
    "application/csv": "text/csv",
}

_SUFFIX_TO_MEDIA_TYPE: dict[str, str] = {
    ".csv": "text/csv",
    ".snip": "application/vnd.sbt.snip",
}


def detect_media_type(medium: RawMedium) -> str:
    if isinstance(medium, PathLike):
        path = Path(medium)
        if path.is_dir() or not path.exists():
            try:
                return _SUFFIX_TO_MEDIA_TYPE[path.suffix]
            except KeyError:
                pass
    with _as_binary_io(medium) as io:
        # Get some data to identify the medium
        data = io.read(2048)  # 2 KiB as recommended in the `python-magic` README.
        io.seek(0)
    # First, we special-case some SBT-specific data formats
    if data.startswith(IQS_SIGNATURE):
        return "application/vnd.sbt.iqs"
    if data.startswith(BDR_SIGNATURE):
        return "application/vnd.sbt.bdr"
    # Second, we fall back on the `python-magic` library.
    result = magic.from_buffer(data, mime=True)
    return _LIBMAGIC_TRANSLATIONS.get(result, result)


@contextmanager
def _as_binary_io(medium: RawMedium) -> Iterator[BinaryIO]:
    if is_binary_io_like(medium):
        yield cast(BinaryIO, medium)
    elif isinstance(medium, PathLike):
        with Path(medium).open("rb") as io:
            yield io
    elif isinstance(medium, bytes):
        yield BytesIO(medium)
    else:
        # We cover all the cases of the `RawMedium` type
        assert False
