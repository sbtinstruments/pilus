from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from ...forge import ForgeIO
from ._transition_fit import FitComplex, TransitionFit

TransitionFitChannel = tuple[FitComplex, ...]


@dataclass(frozen=True)
class BdrAggregateChannel:
    """Aggregation of header and data chunks for a single channel."""

    time_start: int
    time_end: int
    transition_fits: TransitionFitChannel

    def __post_init__(self) -> None:
        if self.time_start > self.time_end:
            raise ValueError("Start time must come before end time")
        if not _is_sorted(self.transition_fits_re) or not _is_sorted(
            self.transition_fits_im
        ):
            raise ValueError("Transition fits must be sorted")

    @property
    def transition_fits_re(self) -> Iterable[TransitionFit]:
        return (fit.re for fit in self.transition_fits)

    @property
    def transition_fits_im(self) -> Iterable[TransitionFit]:
        return (fit.im for fit in self.transition_fits)


BdrAggregateSite = dict[str, BdrAggregateChannel]


@dataclass(frozen=True)
class BdrAggregate(ForgeIO):
    """Aggregation of header and data chunks."""

    sites: dict[str, BdrAggregateSite]


def _is_sorted(values: Iterable[Any]) -> bool:
    # The following is a bit complex because we only iterate over the sequence once.
    # On the other hand, this only requires `Iterable` (and not, e.g., `Sequence`).
    values_iter = iter(values)
    try:
        previous_value = next(values_iter)
    except StopIteration:
        return True
    for value in values:
        if previous_value > value:
            return False
        previous_value = value
    return True
