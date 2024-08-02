from datetime import UTC, datetime

import numpy as np
import polars as pl

from pilus.basic import Wave
from pilus.sbt import BdrAggregate
from pilus.snipdb import SnipDb, SnipRow

from ..forge import FORGE


@FORGE.register_transformer
def iqs_snipdb_polars_df(iqs: SnipDb) -> pl.DataFrame:
    # Data: Column name to series mapping
    data: dict[str, np.ndarray] = {}

    # Index (time)
    rows = iter(iqs.query(SnipRow[Wave]))
    first_row = next(rows)
    wave = first_row.content
    start_time_seconds = wave.metadata.start_time.timestamp()
    duration_s = len(wave.lpcm) * wave.lpcm.time_step_ns * 1e-9

    time = pl.datetime_range(
        start=datetime.fromtimestamp(start_time_seconds, tz=UTC),
        end=datetime.fromtimestamp(start_time_seconds + duration_s, tz=UTC),
        interval=f"{wave.lpcm.time_step_ns}ns",
        closed="left",
    )

    # Ensure that all rows use the same time axis and metadata
    for row in rows:
        wave = row.content
        if (
            wave.metadata != first_row.content.metadata
            or wave.lpcm.time_step_ns != first_row.content.lpcm.time_step_ns
            or wave.lpcm.byte_depth != first_row.content.lpcm.byte_depth
        ):
            raise ValueError("Wave metadata mismatch between rows")

    # Values
    for row in iqs.query(SnipRow[Wave]):
        meta = row.metadata
        site_name = meta.attributes["site"].value
        channel_name = meta.attributes["channel"].value
        part_name = meta.attributes["part"].value
        legendgroup = f"{channel_name}-{part_name}"
        name = f"{site_name}-{legendgroup}"

        # Value axis
        wave = row.content
        assert wave.lpcm.byte_depth == 4
        wave_values = (
            np.frombuffer(wave.lpcm.data, dtype=np.int32) / wave.metadata.max_amplitude
        )
        data[name] = wave_values

    result = pl.DataFrame(data)
    # Truncate the time column to ensure the same length
    return result.with_columns(time=time.head(len(result)))


@FORGE.register_transformer
def bdr_aggregate_to_polars_df(bdr: BdrAggregate) -> pl.DataFrame:
    sites = iter(bdr.sites.values())
    first_site = next(sites)
    channels = iter(first_site.values())
    first_channel = next(channels)

    # TODO: Verify that the start/end times are equal for all sites/channels.
    # Or, overlap all time ranges and use the extremes

    time_start_us = first_channel.time_start
    time_start_s = time_start_us * 1e-6

    time_end_us = first_channel.time_end

    # TODO: Promote time_step_ns to a user-configurable setting
    time_step_ns = 43648  # Arbitrary value (though it coincides with the IQS default)
    time_step_s = time_step_ns * 1e-9

    time = pl.datetime_range(
        start=datetime.fromtimestamp(time_start_s, tz=UTC),
        end=datetime.fromtimestamp(time_end_us * 1e-6, tz=UTC),
        interval=f"{time_step_ns}ns",  # TODO: Something
        closed="left",
        eager=True,
    )

    # Data: Column name to series mapping
    data: dict[str, np.ndarray] = {}

    for site_name, site in bdr.sites.items():
        for channel_name, channel in site.items():
            parts = {
                "re": (channel.transition_fits, channel.transition_fits_re),
                "im": (channel.transition_fits, channel.transition_fits_im),
            }
            for part_name, (fit_complexes, fits) in parts.items():
                # TODO: Add user-configurable setting for what constrant to
                # fill out missing values with.
                fits_values = np.full(len(time), np.nan)

                for fit_complex, fit in zip(fit_complexes, fits, strict=True):

                    def gauss_array(center: float, ts: np.ndarray) -> np.ndarray:
                        return fit.scale * np.exp(
                            -(ts - center)
                            * (ts - center)
                            / (2.0 * fit.width * fit.width)
                        )

                    def _fit_model_array(ts: np.ndarray) -> np.ndarray:
                        transition = gauss_array(
                            fit.center - fit.offset, ts
                        ) - gauss_array(fit.center + fit.offset, ts)
                        return transition + fit.baseline

                    time_start = fit_complex.time_start
                    time_end = fit_complex.time_end
                    start_idx = max(round((time_start - time_start_s) / time_step_s), 0)
                    end_idx = min(
                        round((time_end - time_start_s) / time_step_s),
                        len(time) - 1,
                    )

                    fit_ts = (
                        time[start_idx:end_idx].to_numpy().astype(dtype=np.float64)
                        * 1e-9
                    )
                    fits_values[start_idx:end_idx] = _fit_model_array(fit_ts)

                data[f"{site_name}-{channel_name}-{part_name}"] = fits_values

    return pl.DataFrame({"time": time, **data})
