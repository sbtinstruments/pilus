from __future__ import annotations

from functools import reduce
from pathlib import Path
from typing import Any, ClassVar, Iterable, Optional, Type, TypeVar

from tinydb import TinyDB, where
from tinydb.queries import Query, QueryInstance
from tinydb.storages import MemoryStorage
from typeguard import check_type

from spat.formats import snip

from ..formats.registry import add_deserializer
from ..formats.snip import (
    SnipAttribute,
    SnipAttributeDeclarationMap,
    SnipAttributeMap,
    SnipPart,
    SnipPartMetadata,
)

T = TypeVar("T")


class SnipDb:
    """Immutable, in-memory database of snip parts (deserialized files).

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
        parts: Iterable[SnipPart[Any]],
        attribute_declarations: SnipAttributeDeclarationMap,
    ) -> None:
        self._db = TinyDB(storage=MemoryStorage)
        documents = (
            {
                "value": part.value,
                "name": part.metadata.name,
                "attributes": part.metadata.attributes,
            }
            for part in parts
        )
        self._parts = self._db.table("part")
        self._parts.insert_multiple(documents)
        self._attribute_declarations = attribute_declarations

    def get(
        self,
        type_: Optional[Type[T]] = None,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[SnipPart[T]]:
        """Return the first part that matches the query arguments.

        Returns `None` if there are no matches.
        """
        query = self._args_to_query(type_, name, **kwargs)
        document = self._parts.get(query)
        if document is None:
            return None
        return _doc_to_part(document)

    def search(
        self,
        type_: Optional[Type[T]] = None,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterable[SnipPart[T]]:
        """Return iterable of all parts that matches the query arguments."""
        query = self._args_to_query(type_, name, **kwargs)
        documents = self._parts.search(query)
        return (_doc_to_part(doc) for doc in documents)

    def _args_to_query(
        self,
        type_: Optional[type] = None,
        name: Optional[str] = None,
        **kwargs: str,
    ) -> QueryInstance:
        AttributeNameAndValues = frozenset[tuple[str, SnipAttribute]]
        attributes: Optional[AttributeNameAndValues] = None
        # Consider all keyword arguments as attribute filters
        if kwargs:
            attributes = frozenset(self._attribute_declarations.parse_kwargs(**kwargs))
        # Convert argument to queries
        queries: list[QueryInstance] = []
        if type_ is not None:

            def _test_type(value: Any) -> bool:
                try:
                    check_type("value", value, type_)
                except TypeError:
                    return False
                return True

            queries.append(where("value").test(_test_type))
        if name is not None:
            queries.append(where("name") == name)
        if attributes is not None:

            def _test_attrs(value: SnipAttributeMap) -> bool:
                assert attributes is not None
                name_and_values: AttributeNameAndValues = frozenset(value.items())
                return name_and_values.issuperset(attributes)

            # The typings for `test` assume that it receives a `Mapping`. This is
            # probably the usual case for a TinyDB table. In our case, however, we
            # use in-memory storage so we can store python objects directly (no
            # conversion to dict first). Therefore, the `test` function may receive
            # a custom type and not just a `Mapping`.
            subquery = where("attributes").test(_test_attrs)  # type: ignore[arg-type]
            queries.append(subquery)
        # Raise error if there are no queries
        if not queries:
            raise ValueError("You must provide at least one argument")
        # Combine all queries into one
        query = reduce(Query.__and__, queries)
        return query

    @classmethod
    def from_dir(cls, root: Path) -> SnipDb:
        """Parse directory into an instance of this class."""
        if root.suffix == ".snip":
            return cls.from_snip_dir(root)
        raise ValueError("Can't determine media type from directory alone")

    @classmethod
    def from_snip_dir(cls, root: Path) -> SnipDb:
        """Parse snip directory into an instance of this class."""
        return snip.from_dir(SnipDb, root)

    def __iter__(self) -> Iterable[SnipPart[Any]]:
        """Return iterable of all parts in this database."""
        return (_doc_to_part(doc) for doc in self._parts)


def _doc_to_part(document: dict[str, Any]) -> SnipPart[Any]:
    value = document["value"]
    metadata = SnipPartMetadata(
        name=document["name"], attributes=document["attributes"]
    )
    return SnipPart(value=value, metadata=metadata)


add_deserializer(SnipDb.snip_media_type, from_dir=SnipDb.from_snip_dir)


#   ## Raw data

#   E.g., the data in an IQS file.

#   We split raw data into two files:
#     1. LPCM data in WAVE format.
#        my-data.wav
#     2. Metadata. (data that doesn't fit into the WAVE file itself)
#        my-data.wav-meta.json

#   ### LPCM (Linear Pulse-Code Modulation) data

#   Store main data in a WAVE file

#   Media type: audio/vnd.wave
#   Contains:
#     * sample_rate: int
#     * byte_depth: int
#     * data: bytes

#   ### Metadata

#   Store metadata in a JSON file.

#   Media type: application/vnd.sbt.wav-meta+json
#   Contains: {
#     "startTime": time point (absolute; UTC)
#     "maxValue": max value of PCM data
#   }

#   ## Extrema

#   Store extrema in an array in a JSON file.

#   Media type: application/vnd.sbt.extrema+json
#   Contains: [
#     {
#       "type": "minimum",
#       "time": UTC in microseconds,
#       "value": floating-point value relative to the baseline,
#     },
#     ...
#   ]

#   ## Transitions

#   Store transitions in an array in a JSON file.

#   Media type: application/vnd.sbt.transitions+json
#   Contains: [
#     {
#       "model": {
#         "name": "double-gaussian",
#         "parameters": {
#           "center": time point in microseconds (UTC),
#           "scale": real value,
#           "width": real value,
#           "offset": time duration
#         }
#       }
#     },
#     ...
#   ]
