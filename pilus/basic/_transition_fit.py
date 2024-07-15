from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TransitionFit:
    """Transition fit with model attributes, statistical properties, etc."""

    scale: float
    center: float
    width: float
    baseline: float
    offset: float
    peak_height: float
    # 2*offset
    transition_time: float
    mse: float
    noise: float
    snr: float
    ascend: float
    iterations: int
    origin: int

    def __lt__(self, rhs: TransitionFit) -> bool:
        return self.center < rhs.center

    def __le__(self, rhs: TransitionFit) -> bool:
        return self.center <= rhs.center


@dataclass(frozen=True)
class FitComplex:
    """Transition fit for each complex parts."""

    re: TransitionFit
    im: TransitionFit
    time_start: float
    time_end: float

    def __post_init__(self) -> None:
        if self.time_start > self.time_end:
            raise ValueError("Start time must come before end time")
        if not self.time_start <= self.re.center <= self.time_end:
            raise ValueError(
                "Real part center must be within the overall time interval"
            )
        if not self.time_start <= self.im.center <= self.time_end:
            raise ValueError(
                "Imaginary part center must be within the overall time interval"
            )

    def __lt__(self, rhs: FitComplex) -> bool:
        return min(self.re.center, self.im.center) < min(rhs.re.center, rhs.im.center)

    def __le__(self, rhs: FitComplex) -> bool:
        return min(self.re.center, self.im.center) <= min(rhs.re.center, rhs.im.center)
