from dataclasses import dataclass
from inspect import signature
from typing import Any, Callable

MergeFunc = Callable[[Any, Any], Any]


@dataclass(frozen=True)
class Merger:
    func: MergeFunc
    arg_positons: dict[Any, int]

    def __call__(self, *args: Any) -> Any:
        values = list(range(len(args)))
        for arg in args:
            pos = self.arg_positons[type(arg)]
            values[pos] = arg
        return self.func(*values)


# Global dict of all registered mergers
MERGERS: dict[frozenset[Any], Merger] = dict()


def register_merger(func: MergeFunc) -> None:
    """Register the given merger function."""
    sig = signature(func)
    arg_types: list[Any] = [p.annotation for p in sig.parameters.values()]
    input_types: frozenset[Any] = frozenset(arg_types)
    # Early out on invalid merger
    if len(input_types) != 2:
        raise ValueError("The merger must take exactly two arguments")
    # Early out on conflict
    if input_types in MERGERS:
        raise ValueError(
            f'There already is a merger for the "{input_types}" input pair'
        )

    arg_positions = {at: i for i, at in enumerate(arg_types)}
    merger = Merger(func, arg_positions)
    MERGERS[input_types] = merger
