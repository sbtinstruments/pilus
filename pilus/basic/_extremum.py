from datetime import datetime
from enum import Enum
from typing import Tuple

from ..formats.json import from_json_data
from ..formats.registry import add_deserializer
from ..model import Model


class ExtremumType(Enum):
    """An extremum can either be a minimum or a maximum."""

    # Assign values for serialization purposes
    MINIMUM = "minimum"
    MAXIMUM = "maximum"


class Extremum(Model):
    """Time-indexed extremum with floating-point value."""

    time_point: datetime
    value: float
    type_: ExtremumType


Extrema = Tuple[Extremum, ...]


add_deserializer(
    "application/vnd.sbt.extrema+json",
    from_data=lambda data: from_json_data(Extrema, data),
)
