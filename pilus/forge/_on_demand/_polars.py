from .._forge import Forge
from .._global_forge import FORGE


@FORGE.call_on_demand(
    type_repr_any_of=("<class 'polars.dataframe.frame.DataFrame'>",),
)
def register_polars(forge: Forge) -> None:
    """Register morphers (serializers/deserializers/etc.) in the given forge.

    Uses the global forge if you don't explicitly provide a forge.
    """
    if forge is not FORGE:
        raise NotImplementedError
    # Indirectly, the following `import` registers all morphers in the
    # global `FORGE` instance.
    from ... import polars
