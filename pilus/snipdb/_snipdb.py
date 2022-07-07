from __future__ import annotations

from functools import reduce
from pathlib import Path
from typing import Any, ClassVar, Iterable, Iterator, Optional, Type, TypeVar

from tinydb import TinyDB, where
from tinydb.queries import Query, QueryInstance
from tinydb.storages import MemoryStorage
from typeguard import check_type

from .._magic import Medium
from ..forge import FORGE, ForgeIO
from ._snip_attribute_declaration_map import SnipAttrDeclMap
from ._snip_attributes import SnipAttr
from ._snip_part import SnipPart
from ._snip_part_metadata import SnipAttributeMap, SnipPartMetadata

T = TypeVar("T")


class SnipDb(ForgeIO):
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
        parts: Iterable[SnipPart[Any]] = tuple(),
        attr_decls: SnipAttrDeclMap = SnipAttrDeclMap(),
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
        # Ensure that the parts' attributes have corresponding declarations in the
        # given declaration map.
        attributes = (a for p in self for a in p.metadata.attributes.values())
        if not attr_decls.has_declarations_for(attributes):
            raise ValueError("A part has an undeclared attribute")
        self._attr_decls = attr_decls

    def get(
        self, type_: Optional[Type[T]] = None, name: Optional[str] = None, **kwargs: Any
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
        self, type_: Optional[Type[T]] = None, name: Optional[str] = None, **kwargs: Any
    ) -> Iterable[SnipPart[T]]:
        """Return iterable of all parts that matches the query arguments."""
        query = self._args_to_query(type_, name, **kwargs)
        documents = self._parts.search(query)
        return (_doc_to_part(doc) for doc in documents)

    def _args_to_query(
        self, type_: Optional[type] = None, name: Optional[str] = None, **kwargs: str
    ) -> QueryInstance:
        AttributeNameAndValues = frozenset[tuple[str, SnipAttr]]
        attributes: Optional[AttributeNameAndValues] = None
        # Consider all keyword arguments as attribute filters
        if kwargs:
            attributes = frozenset(self._attr_decls.parse_kwargs(**kwargs))
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
    def from_dir(cls, directory: Path, *, media_type: Optional[str] = None) -> SnipDb:
        """Deserialize directory into an instance of this class."""
        input_medium = Medium.from_raw(directory, media_type=media_type)
        return FORGE.deserialize(input_medium, cls)

    def __iter__(self) -> Iterator[SnipPart[Any]]:
        """Return iterator of all parts in this database."""
        return (_doc_to_part(doc) for doc in self._parts)


def _doc_to_part(document: dict[str, Any]) -> SnipPart[Any]:
    value = document["value"]
    metadata = SnipPartMetadata(
        name=document["name"], attributes=document["attributes"]
    )
    return SnipPart(value=value, metadata=metadata)
