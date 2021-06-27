from datetime import datetime
from enum import Enum
from typing import Tuple

from ..formats import register_parsers
from ..model import Model, from_json_data


class ExtremumType(Enum):
    # Assign values for serialization purposes
    MINIMUM = "Minimum"
    MAXIMUM = "Maximum"


class Extremum(Model):
    time_point: datetime
    value: float
    type_: ExtremumType


Extrema = Tuple[Extremum, ...]


register_parsers(
    "application/vnd.sbt.extrema+json",
    from_data=lambda data: from_json_data(Extrema, data),
)
