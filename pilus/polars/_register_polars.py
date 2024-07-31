from ..forge import FORGE, Forge, Morpher


def register_polars(forge: Forge | None = None) -> None:
    """Register morphers (serializers/deserializers/etc.) for the given forge.

    Uses the global forge if you don't explicitly provide a forge.
    """
    if forge is None:
        forge = FORGE

    # Avoid top-level imports until we call this registraiton function. This way,
    # the following dependencies become optional
    import polars as pl

    from pilus.basic import BdrAggregate
    from pilus.snipdb._snipdb import SnipDb

    from ._to_polars_df import bdr_aggregate_to_polars_df, iqs_snipdb_polars_df

    forge.add_morpher(
        Morpher(
            input=SnipDb,
            output=pl.DataFrame,
            func=iqs_snipdb_polars_df,
        )
    )

    forge.add_morpher(
        Morpher(
            input=BdrAggregate,
            output=pl.DataFrame,
            func=bdr_aggregate_to_polars_df,
        )
    )


FORGE.lazy_registration["<class 'polars.dataframe.frame.DataFrame'>"] = register_polars
