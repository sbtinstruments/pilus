from typing import Any

from ._merger import MergeFunc, Merger

# Global dict of all registered mergers
MERGERS: dict[frozenset[Any], Merger] = dict()


def register_merger(func: MergeFunc) -> None:
    """Register the given merger function.

    We automatically deduce the merged types from the function signature. Therefore,
    `func` must have a type annotation for all arguments.
    """
    merger = Merger(func)
    arg_types = merger.arg_types
    # Early out on conflict
    if arg_types in MERGERS:
        raise ValueError(f'There already is a merger for the "{arg_types}" types')
    MERGERS[arg_types] = merger
