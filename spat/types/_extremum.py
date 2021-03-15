from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Tuple

from pydantic.main import BaseModel


class ExtremumType(Enum):
    # Assign values for serialization purposes
    MINIMUM = "Minimum"
    MAXIMUM = "Maximum"


class Extremum(BaseModel):
    time_point: datetime
    value: float
    type_: ExtremumType

    class Config:
        allow_mutation = False


Extrema = Tuple[Extremum]
