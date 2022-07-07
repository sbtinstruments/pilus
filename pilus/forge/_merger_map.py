from typing import Any, Optional

from ._merger import Merger

TypeSet = frozenset[type]


class MergerMap:
    """Container for mergers."""

    def __init__(self) -> None:
        self._data: dict[TypeSet, Merger] = dict()

    def get_merger(self, type_set: TypeSet, *args: Any) -> Optional[Merger]:
        """Get the merger that corresponds to the given types.

        Returns `default` if there is no such merger.
        """
        return self._data.get(type_set, *args)

    def add_merger(self, merger: Merger) -> None:
        """Add the given merger function to the global registry.

        We automatically deduce the merged types from the function signature. Therefore,
        `func` must have a type annotation for all arguments.
        """
        arg_types = merger.arg_types
        # Early out on conflict
        if arg_types in self._data:
            raise ValueError(f'There already is a merger for the "{arg_types}" types')
        self._data[arg_types] = merger
