from .._forge import Forge
from .._global_forge import FORGE


@FORGE.call_on_demand(
    type_repr_any_of=(
        "<class 'pilus.sbt.model._bdr_aggregate.BdrAggregate'>",
        "<class 'pilus.sbt.model._iqs_aggregate.IqsAggregate'>",
    ),
    media_type_any_of=(
        "application/vnd.sbt.iqs",
        "application/vnd.sbt.bdr",
        "application/vnd.sbt.extrema+json",
    ),
)
def register_pilus_sbt(forge: Forge) -> None:
    """Register morphers (serializers/deserializers/etc.) in the given forge.

    Uses the global forge if you don't explicitly provide a forge.
    """
    if forge is not FORGE:
        raise NotImplementedError
    # Indirectly, the following `import` registers all morphers in the
    # global `FORGE` instance.
    #
    # Register the basic types as well. This way, we pull in generic
    # morphers such as "`SimpleTable` to `text/csv`" that we, in turn, can use
    # to convert between BDR and CSV.
    from ... import basic, sbt
