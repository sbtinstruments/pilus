from __future__ import annotations

from collections import defaultdict
from functools import reduce
from typing import (
    Any,
    Iterable,
    Iterator,
    TypeVar,
)

from tinydb import TinyDB, where
from tinydb.queries import Query, QueryInstance
from tinydb.storages import MemoryStorage
from tinydb.table import Document
from typeguard import check_type

from ..errors import (
    PilusMissingMorpherError,
    PilusMultipleResultsFound,
    PilusNoResultFound,
)
from ..forge import FORGE
from ._snip_attribute_declaration_map import SnipAttrDeclMap
from ._snip_attributes import SnipAttr
from ._snip_row import SnipRow
from ._snip_row_metadata import SnipAttributeMap, SnipRowMetadata

T = TypeVar("T")
AttributeNameAndValues = frozenset[tuple[str, SnipAttr]]


class SnipDbCore:
    def __init__(
        self,
        rows: Iterable[SnipRow[Any]] = tuple(),
        attr_decls: SnipAttrDeclMap = SnipAttrDeclMap(),
    ) -> None:
        self._db = TinyDB(storage=MemoryStorage)
        documents = (
            {
                "content": row.content,
                "name": row.metadata.name,
                "attributes": row.metadata.attributes,
                "suffixes": row.metadata.suffixes,
            }
            for row in rows
        )
        self._snippets = self._db.table("snippets")
        self._snippets.insert_multiple(documents)
        # Ensure that the snippets' attributes have corresponding declarations in the
        # given declaration map.
        attributes = (a for p in self for a in p.metadata.attributes.values())
        if not attr_decls.has_declarations_for(attributes):
            raise ValueError("A snippet has an undeclared attribute")
        self._attr_decls = attr_decls

    def get_one(self, type_: type[T], *args: Any, **kwargs: Any) -> SnipRow[T]:
        """Return the unique row that matches the query arguments.

        Raises `PilusNoResultFound` if there is no such row.
        Raises `PilusMultipleResultsFound` if there are multiple rows.

        Use `get_first` if you don't care about uniqueness and just want the first
        matching row.
        """
        results = iter(self.query(type_, *args, **kwargs))
        # Get the first result
        try:
            first_result = next(results)
        except StopIteration as exc:
            raise PilusNoResultFound from exc
        # Make sure that there are no more results (i.e., that the first result
        # is unique).
        if next(results, None) is not None:
            raise PilusMultipleResultsFound
        return first_result

    def get_first(self, type_: type[T], *args: Any, **kwargs: Any) -> SnipRow[T] | None:
        """Return the first row that matches the query arguments.

        Returns `None` if there are no matches.
        """
        results = iter(self.query(type_, *args, **kwargs))
        return next(results, None)

    def query(self, type_: type[T], *args: Any, **kwargs: Any) -> Iterable[SnipRow[T]]:
        """Return all rows (if any) that match the given arguments.

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
        # Rows that are already instances of the given type
        if rows := tuple(self._get_rows_of_type(type_, *args, **kwargs)):
            return rows
        # Rows that we can *reshape* into the given type
        if rows := tuple(self._reshape_rows_to_type(type_, *args, **kwargs)):
            return rows
        # Rows that we can *combine* into the given type
        if rows := tuple(self._combine_rows_to_type(type_, *args, **kwargs)):
            return rows
        return tuple()

    def _get_rows_of_type(
        self, type_: type[T], *args: Any, **kwargs: Any
    ) -> Iterable[SnipRow[T]]:
        query = self._args_to_query(type_, *args, **kwargs)
        documents = self._snippets.search(query)
        for document in documents:
            yield _doc_to_row(document)

    def _reshape_rows_to_type(
        self, type_: type[T], *args: Any, **kwargs: Any
    ) -> Iterable[SnipRow[T]]:
        """Reshape each row into the given type (skipping ahead if impossible)."""
        # Get all rows that match the given arguments *regardless of the type*.
        #
        # TODO: Make this more performant. Do not simply query across all types. For now,
        # however, this does not matter at all since all snip DBs that we have on record
        # has at most 10 entries. In other words, query performance is not an issue.
        try:
            query = self._args_to_query(None, *args, **kwargs)
        except ValueError:  # Empty query
            documents = self._snippets.all()
        else:
            documents = self._snippets.search(query)

        for document in documents:
            content = document["content"]
            try:
                reshape_func = FORGE.get_reshape_func(content, type_)
            except PilusMissingMorpherError:
                continue
            converted_content = reshape_func(content)
            yield _doc_to_row(
                {
                    **document,
                    "content": converted_content,
                }
            )

    def _combine_rows_to_type(
        self, type_: type[T], *args: Any, **kwargs: Any
    ) -> Iterable[SnipRow[T]]:
        """Combine rows into the given type.

        Considers all rows that match the given metadata (name and attributes).
        """
        # Find all combiners that outputs the given type (regardless of input types)
        combiners = FORGE._combiners.get_combiners(output_type=type_)

        # Go through each combiner and see if we can produce relevant inputs
        # for said combiner.
        for combiner in combiners:
            try:
                # Note that `get_one` is a high-level call. That is, it'll
                # automatically reshape/combine any documents into the required
                # type.
                input_rows: list[SnipRow[Any]] = [
                    self.get_one(arg_type, *args, **kwargs)
                    for arg_type in combiner.arg_types
                ]
            except (PilusNoResultFound, PilusMultipleResultsFound):
                # There is one ore more missing input types. Try the next combiner.
                continue

            # Only combine rows if their metadata mataches
            meta_to_content: defaultdict[SnipRowMetadata, list[Any]] = defaultdict(list)
            for row in input_rows:
                meta_to_content[row.metadata.exclude_tracing()].append(row.content)

            # For each matching set of metadata, try to combine the rows
            for metadata, content_list in meta_to_content.items():
                try:
                    content = combiner(*content_list)
                except ValueError:
                    continue
                yield SnipRow(metadata=metadata, content=content)

    def _args_to_query(
        self, type_: type | None = None, *args: Any, **kwargs: str
    ) -> QueryInstance:
        attributes: AttributeNameAndValues | None = None
        # Consider all keyword arguments as attribute filters
        if kwargs:
            attributes = frozenset(self._attr_decls.parse_kwargs(**kwargs))
        # Convert argument to queries
        queries: list[QueryInstance] = []
        if type_ is not None:

            def _test_type(content: Any) -> bool:
                try:
                    check_type("content", content, type_)
                except TypeError:
                    return False
                return True

            queries.append(where("content").test(_test_type))
        for arg in args:
            if not isinstance(arg, QueryInstance):
                raise TypeError
            queries.append(arg)
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

    def __iter__(self) -> Iterator[SnipRow[Any]]:
        """Return iterator of all rows in this database."""
        return (_doc_to_row(doc) for doc in self._snippets)


def _doc_to_row(document: dict[str, Any]) -> SnipRow[Any]:
    content = document["content"]
    metadata = SnipRowMetadata(
        name=document["name"],
        attributes=document["attributes"],
        suffixes=document["suffixes"],
    )
    return SnipRow(content=content, metadata=metadata)
