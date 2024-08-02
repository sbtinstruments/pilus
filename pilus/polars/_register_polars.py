from ..forge import FORGE, Forge


def register_polars(forge: Forge | None = None) -> None:
    """Register morphers (serializers/deserializers/etc.) in the given forge.

    Uses the global forge if you don't explicitly provide a forge.
    """
    if forge is None:
        forge = FORGE

    # Indirectly, the following `import`s pull in the polars package. Therefore,
    # we do *not* import them globally but inside this registrion function instead.
    # This way, the heavy `import` occurs on-demand.
    from ._to_polars_df import bdr_aggregate_to_polars_df, iqs_snipdb_polars_df
    from ._from_polars_df import from_polars_df_to_iqs_snipdb

    forge.register_transformer(iqs_snipdb_polars_df)
    forge.register_transformer(bdr_aggregate_to_polars_df)
    forge.register_transformer(from_polars_df_to_iqs_snipdb)


FORGE.register_on_demand(
    register_polars, type_repr="<class 'polars.dataframe.frame.DataFrame'>"
)
