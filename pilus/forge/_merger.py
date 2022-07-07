from dataclasses import dataclass, field
from inspect import Signature, isclass, signature
from typing import Any, Callable, cast, get_type_hints

from ..utility import find_duplicates

MergeFunc = Callable[..., Any]


@dataclass(frozen=True)
class Merger:
    """Callable that merges multiple objects into one."""

    func: MergeFunc
    arg_positions: dict[type, int] = field(init=False)

    def __post_init__(self) -> None:
        # Extract the type annotations of `func`. Note that we use `get_type_hints`,
        # which correctly evaluates forward references encoded as string literals.
        # In other words, `get_type_hints` handles the effects of
        # `from __future__ import annotations`.
        type_hints = get_type_hints(self.func)
        arg_types: list[Any] = [
            hint for name, hint in type_hints.items() if name != "return"
        ]
        # Make sure that all type annotations are actual types and not, e.g.,
        # unions of types.
        non_simple_arg_types = (
            arg_type for arg_type in arg_types if not isclass(arg_type)
        )
        for nonsimple_arg_type in non_simple_arg_types:
            raise ValueError(
                "Merge func must use simple (e.g., non-union) type annotations for all"
                f' its arguments. Type "{nonsimple_arg_type}" is non-simple.'
            )
        arg_types = cast(list[type], arg_types)
        # We want to ensure that all `func`'s arguments are typed. Unfortunately,
        # `get_type_hints` doesn't include un-typed arguments. Therefore, we also
        # use `signature` to get all arguments.
        # Note that we can't simply use `signature` in place of `get_type_hints`
        # because the former doesn't evaluate forward references encoded as string
        # literals (but the latter does).
        parameters = signature(self.func).parameters
        if any(p.annotation is Signature.empty for p in parameters.values()):
            raise ValueError("Merge func must have a type annotation for all arguments")
        # Ensure that `func` has at least two arguments
        if len(arg_types) < 2:
            raise ValueError("Merge func must have at least two arguments")
        # Ensure that `func`'s arguments has distinct type annotations (no duplicates).
        for duplicate_type in find_duplicates(arg_types):
            raise ValueError(
                f'Merge function has multiple arguments of type "{duplicate_type}". '
                "Argument types must be unique."
            )
        # Remember the argument positions based on their type. We need this in
        # `__call__`, since it can take arguments in any order (for convenience).
        arg_positions = {arg_type: i for i, arg_type in enumerate(arg_types)}
        # We use `object.__setattr__` since this class is frozen
        object.__setattr__(self, "arg_positions", arg_positions)

    @property
    def arg_types(self) -> frozenset[type]:
        """Return a set of the argument types."""
        return frozenset(self.arg_positions)

    def __call__(self, *args: Any) -> Any:
        """Merge the given objects.

        For convenience, you can give the arguments in any order. We automatically
        re-order the arguments before we pass them along to the underlying `func`.
        """
        return self.func(*self._order_args(*args))

    def _order_args(self, *args: Any) -> list[Any]:
        # Ensure that the given arguments have unique types
        arg_types = (type(arg) for arg in args)
        for duplicate_type in find_duplicates(arg_types):
            raise ValueError(
                f'There are multiple arguments of type "{duplicate_type}". '
                "Argument types must be unique."
            )
        # Ensure that the number of arguments matches the signature of `func`
        actual_arg_count = len(args)
        expected_arg_count = len(self.arg_positions)
        if actual_arg_count != expected_arg_count:
            raise ValueError(
                f"Expected {expected_arg_count} arguments but got {actual_arg_count}"
            )
        # Allocate a result vector
        values: list[Any] = [None for _ in args]
        # Insert each object into `values` so that their order matches `func`'s
        # signature.
        for arg in args:
            # Match argument position based on type
            pos = self.arg_positions[type(arg)]
            values[pos] = arg
        return values
