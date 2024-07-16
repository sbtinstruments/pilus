from datetime import datetime
from enum import Enum, unique

from pydantic import TypeAdapter

from .._magic import MediumSpec
from ..forge import FORGE, Morpher
from ..model import FrozenModel


@unique
class ExtremumType(Enum):
    """An extremum can either be a minimum or a maximum."""

    # Assign values for serialization purposes
    MINIMUM = "minimum"
    MAXIMUM = "maximum"


class Extremum(FrozenModel):
    """Time-indexed extremum with floating-point value."""

    time_point: datetime
    value: float
    type_: ExtremumType


Extrema = tuple[Extremum, ...]


FORGE.add_morpher(
    Morpher(
        input=MediumSpec(
            raw_type=bytes, media_type="application/vnd.sbt.extrema+json"),
        output=Extrema,
        func=TypeAdapter(Extrema).validate_json,

    )
)
