from .._forge import Forge
from .._global_forge import FORGE


@FORGE.call_on_demand(
    type_repr_any_of=(
        "<class 'pilus.basic.model._lpcm.Lpcm'>",
        "<class 'pilus.basic.model._wave.Wave'>",
        "<class 'pilus.basic.model._wave_meta.WaveMeta'>",
        "list[list[typing.Any]]",
    ),
    media_type_any_of=(
        "application/vnd.sbt.box.manifest+json",
        "audio/vnd.wave",
        "application/vnd.sbt.wave-meta+json",
        # Note that we intentionally do not add "text/csv" even though
        # we got the `table_to_csv` serializer for it. It's too generic
        # for this "load on demand" feature.
    ),
)
def register_pilus_basic(forge: Forge) -> None:
    """Register morphers (serializers/deserializers/etc.) in the given forge.

    Uses the global forge if you don't explicitly provide a forge.
    """
    if forge is not FORGE:
        raise NotImplementedError
    # Indirectly, the following `import` registers all morphers in the
    # global `FORGE` instance.
    from ... import basic
