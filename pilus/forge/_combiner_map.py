from collections.abc import Iterable

from ._combiner import Combiner

TypeSet = frozenset[type]


class CombinerMap:
    """Container for combiners."""

    def __init__(self) -> None:
        self._data: dict[TypeSet, Combiner] = dict()

    def get_combiners(
        self,
        *,
        input_types: TypeSet | None = None,
        output_type: type | None = None,
    ) -> Iterable[Combiner]:
        """Get the combiner that corresponds to the given types.

        If you query by `output_type`, then we return the first matching combiner.

        Returns `None` if there is no such combiner.
        """
        if input_types is not None and output_type is not None:
            raise NotImplementedError

        if input_types is not None:
            try:
                yield self._data[input_types]
            except KeyError:
                return

        if output_type is not None:
            yield from (
                combiner
                for combiner in self._data.values()
                if combiner.output_type == output_type
            )
            return

        raise ValueError("You must specify one of `input_types` or `output_type`")

    def add_combiner(self, combiner: Combiner) -> None:
        """Add the given combiner function to the global registry.

        We automatically deduce the combined types from the function signature. Therefore,
        `func` must have a type annotation for all arguments.
        """
        arg_types = combiner.arg_types
        # Early out on conflict
        if arg_types in self._data:
            raise ValueError(f'There already is a combiner for the "{arg_types}" types')
        self._data[arg_types] = combiner
