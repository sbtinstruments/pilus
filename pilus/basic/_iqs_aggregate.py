from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..forge import ForgeIO


@dataclass(frozen=True)
class IqsChannelHeader:
    """Used to interpret raw binary channel data."""

    time_step_ns: int
    byte_depth: int
    max_amplitude: int


@dataclass(frozen=True)
class IqsChannelData:
    """Raw binary channel data split into complex parts."""

    re: bytes
    im: bytes

    def __post_init__(self) -> None:
        if len(self.re) != len(self.im):
            raise ValueError("The two complex parts must have the same length")


@dataclass(frozen=True)
class IqsAggregateChannel(IqsChannelData, IqsChannelHeader):
    """Aggregation of header and data chunks for a single channel."""


IqsAggregateSite = dict[str, IqsAggregateChannel]


@dataclass(frozen=True)
class IqsAggregate(ForgeIO):
    """Aggregation of header and data chunks."""

    start_time: datetime
    duration_ns: int
    sites: dict[str, IqsAggregateSite]
