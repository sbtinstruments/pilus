from typing import Iterable

import numpy as np
import polars as pl

from pilus.basic import Lpcm, Wave, WaveMeta
from pilus.forge import FORGE
from pilus.snipdb import (
    SnipAttrDecl,
    SnipAttrDeclMap,
    SnipDb,
    SnipEnumDecl,
    SnipRow,
    SnipRowMetadata,
    create_attribute_map,
)

# NOTE: value fixed in baxter
_BYTE_DEPTH = 4
# NOTE: value fixed by sbt_lock_amp
_MAX_AMPLITUDE = 1784331945


@FORGE.register_transformer
def from_polars_df_to_iqs_snipdb(iqs: pl.DataFrame) -> SnipDb:
    attr_decls = _from_polar_df_to_attr_decls(iqs)
    snip_rows = _from_polar_df_to_snip_rows(iqs, attr_decls)
    return SnipDb(snip_rows, attr_decls)


def _from_polar_df_to_attr_decls(iqs: pl.DataFrame) -> SnipAttrDeclMap:
    """Extract attribute declarations from an IQS aggregate."""
    # Go through the site-channel hierarchy and record the names along the way
    site_enum_values: set[str] = set()
    channel_enum_values: set[str] = set()
    part_enum_values: set[str] = set()
    for column in iqs.columns:
        if column == "time":
            continue
        site, channel, part = column.split("-")
        site_enum_values.add(site)
        channel_enum_values.add(channel)
        part_enum_values.add(part)
    # Convert all site and channel names into enum attributes
    root: dict[str, SnipAttrDecl] = {
        "site": SnipEnumDecl.from_args(values=site_enum_values),
        "channel": SnipEnumDecl.from_args(values=channel_enum_values),
        "part": SnipEnumDecl.from_args(values=part_enum_values),
    }
    return SnipAttrDeclMap(root=root)


def _from_polar_df_to_snip_rows(
    iqs: pl.DataFrame, attr_decls: SnipAttrDeclMap
) -> Iterable[SnipRow[Wave]]:
    time = iqs.get_column("time")
    # HACK: We assumed that the sampling rate is uniform across the timeseries
    time_step_ns = time[:2].diff(null_behavior="drop").cast(int).item()
    for series in iqs:
        name = series.name
        if name == "time":
            continue
        array = series.to_numpy()
        site, channel, part = name.split("-")
        array_bytes = np.array(array * _MAX_AMPLITUDE, np.int32).tobytes()
        lpcm = Lpcm(_BYTE_DEPTH, time_step_ns, array_bytes)
        wave_metadata = WaveMeta(start_time=time[0], max_amplitude=_MAX_AMPLITUDE)
        wave = Wave(lpcm, wave_metadata)
        attributes = create_attribute_map(
            attr_decls,
            site=site,
            channel=channel,
            part=part,
        )
        metadata = SnipRowMetadata(name=name, attributes=attributes)
        yield SnipRow(content=wave, metadata=metadata)
