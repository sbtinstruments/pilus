from typing import Any, Optional

from ._merger import MergeFunc, Merger

Key = frozenset[Any]

# Global dict of all registered mergers
_MERGERS: dict[Key, Merger] = dict()


def get_merger(type_set: Key, *args: Any) -> Optional[Merger]:
    """Get the merger that corresponds to the given types.

    Returns `default` if there is no such merger.
    """
    return _MERGERS.get(type_set, *args)


def add_merger(func: MergeFunc) -> None:
    """Add the given merger function to the global registry.

    We automatically deduce the merged types from the function signature. Therefore,
    `func` must have a type annotation for all arguments.
    """
    merger = Merger(func)
    arg_types = merger.arg_types
    # Early out on conflict
    if arg_types in _MERGERS:
        raise ValueError(f'There already is a merger for the "{arg_types}" types')
    _MERGERS[arg_types] = merger
