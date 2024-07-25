import math
from dataclasses import astuple, fields
from typing import Any, Iterator

from ..basic import (
    BdrAggregate,
    BdrAggregateChannel,
    FitComplex,
    SimpleTable,
    TransitionFit,
    TransitionFitChannel,
)
from ..forge import FORGE, Morpher

_COLUMN_NAMES: tuple[str, ...] = (
    "site",
    "channel",
    "part",
    "time_start",
    "time_end",
    *(field.name for field in fields(TransitionFit)),
)


def bdr_to_simple_table(aggregate: BdrAggregate) -> SimpleTable:
    """Extract attribute declarations from an IQS aggregate."""
    return list(_bdr_to_rows(aggregate))


def _bdr_to_rows(aggregate: BdrAggregate) -> Iterator[list[Any]]:
    # Header row
    yield list(_COLUMN_NAMES)
    # Data rows
    for site_name, site in aggregate.sites.items():
        for channel_name, channel in site.items():
            for fit_complex in channel.transition_fits:
                yield [
                    site_name,
                    channel_name,
                    "re",
                    fit_complex.time_start,
                    fit_complex.time_end,
                    *astuple(fit_complex.re),
                ]
                yield [
                    site_name,
                    channel_name,
                    "im",
                    fit_complex.time_start,
                    fit_complex.time_end,
                    *astuple(fit_complex.im),
                ]


FORGE.add_morpher(
    Morpher(
        input=BdrAggregate,
        output=SimpleTable,
        func=bdr_to_simple_table,
    )
)
