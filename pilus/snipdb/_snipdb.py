from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar, Iterable, Iterator, TypeVar

from pydantic.v1.utils import lenient_issubclass

from .._magic import Medium
from ..forge import FORGE, ForgeIO
from ._snip_attribute_declaration_map import SnipAttrDeclMap
from ._snip_row import SnipRow
from ._snipdb_core import SnipDbCore

T = TypeVar("T")


class SnipDb(ForgeIO):
    """Immutable, in-memory database of files in a directory.

    Examples:
        /manifest.json
        {
            "extensionToMediaType": {
            ".wav": "audio/vnd.wave",
            ".wav-meta.json": "application/vnd.sbt.wav-meta+json",
            ".extrema.json": "application/vnd.sbt.extrema+json",
            ".transitions.json": "application/vnd.sbt.transitions+json",
            ".alg.json": "application/vnd.sbt.alg+json",
            }
        }

        /attributes.json
        {
            "enums": {
                "site": {
                    "values": ["site0", "site1"]
                },
                "frequency": {
                    "values": ["hf", "lf"]
                },
                "part": {
                    "values": ["real", "imaginary"]
                },
                "settings": {
                    "values": ["production", "tuned-for-bacillus"]
                }
            }
        }

        ### /data/{name}--{attr0}--{attr1}--{attr2}.{type}

        /data/settings--general.alg.json
        /data/settings--tuned-for-bacillus.alg.json
        /data/diff--site0--hf--re.wav
        /data/diff--site0--hf--re.wav-meta.json
        /data/diff--site0--hf--re--general.extrema.json
        /data/diff--site0--hf--re--general.transitions.json
        /data/diff--site0--hf--re--tuned-for-bacillus.extrema.json
        /data/diff--site0--hf--re--tuned-for-bacillus.transitions.json
        /data/diff--site0--hf--im.wav
        /data/diff--site0--hf--im.wav-meta.json
        ...
        /data/diff--site1--lf--im--tuned-for-bacillus.transitions.json

    """

    snip_media_type: ClassVar[str] = "application/vnd.sbt.snip"

    def __init__(
        self,
        rows: Iterable[SnipRow[Any]] = tuple(),
        attr_decls: SnipAttrDeclMap = SnipAttrDeclMap(),
    ) -> None:
        self._core = SnipDbCore(rows, attr_decls)

    @classmethod
    def from_dir(cls, directory: Path, *, media_type: str | None = None) -> SnipDb:
        """Deserialize directory into an instance of this class."""
        input_medium = Medium.from_raw(directory, media_type=media_type)
        return FORGE.deserialize(input_medium, cls)

    def get_one(self, type_: type[T], *args: Any, **kwargs: Any) -> T:
        """Return the unique object that matches the query arguments.

        Wrap `type_` as `SnipRow[type_]` if you also want the metadata.

        Raises `PilusNoResultFound` if there is no such object.
        Raises `PilusMultipleResultsFound` if there are multiple objects.

        Use `get_first` if you don't care about uniqueness and just want the first
        matching object.
        """
        row = self._core.get_one(_content_type(type_), *args, **kwargs)
        return _row_to_type(row, type_)  # type: ignore[return-value]

    def get_first(self, type_: type[T], *args: Any, **kwargs: Any) -> T | None:
        """Return the first row that matches the query arguments.

        Wrap `type_` as `SnipRow[type_]` if you also want the metadata.

        Returns `None` if there are no matches.
        """
        row = self._core.get_first(_content_type(type_), *args, **kwargs)
        return None if row is None else _row_to_type(row, type_)  # type: ignore[arg-type, return-value]

    def query(self, type_: type[T], *args: Any, **kwargs: Any) -> Iterable[T]:
        """Return all rows (if any) that match the given arguments.

        Wrap `type_` as `SnipRow[type_]` if you also want the metadata.

        This function goes through *all* rows and yields:

         * Instances of `type_` that we can return directly.
         * A medium (file path, IO stream, pointer to memory, ...) that we can
           deserialize/transform into `type_`.
         * A collection of shapes (instance or medium) that we can combine into
           `type_`.

        For the last case (combination) we even look for *any* shape that we can
        deserialize/transform into some intermediary type that we then combine
        into `type_`!
        """
        rows = self._core.query(_content_type(type_), *args, **kwargs)
        return (_row_to_type(row, type_) for row in rows)  # type: ignore[misc]

    def __iter__(self) -> Iterator[SnipRow[Any]]:
        """Return iterator of all rows in this database."""
        return self._core.__iter__()


def _row_to_type(row: SnipRow[T], type_: type[T] | type[SnipRow[T]]) -> T | SnipRow[T]:
    if lenient_issubclass(type_, SnipRow):
        return row
    return row.content


def _content_type(type_: type[T] | type[SnipRow[T]]) -> type[T]:
    if lenient_issubclass(type_, SnipRow):
        assert issubclass(type_, SnipRow)
        content_field = type_.model_fields["content"]
        core_type = content_field.annotation
        assert core_type is not None
        return core_type
    return type_  # type: ignore[return-value]
