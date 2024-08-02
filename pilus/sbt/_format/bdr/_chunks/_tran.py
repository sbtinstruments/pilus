from __future__ import annotations

from dataclasses import dataclass
from typing import Any, BinaryIO, ClassVar

from .....errors import PilusDeserializeError
from ...._model import FitComplex, TransitionFit, TransitionFitChannel
from ..._io import read_double, read_int

SiteData = dict[str, TransitionFitChannel]

FIT_SIZE_IN_BYTES = 400


@dataclass(frozen=True)
class TranChunk:
    """Chunk with transition data."""

    type_: ClassVar[bytes] = b"tRAN"

    site_data: SiteData

    @classmethod
    def from_io(cls, io: BinaryIO, **kwargs: Any) -> TranChunk:
        """Deserialize the IO stream into a tRAN chunk.

        May raise `IqsError` or one of its derivatives.
        """
        data_length = kwargs["data_length"]
        assert isinstance(data_length, int)
        channel_names: tuple[str] = kwargs["channel_names"]
        assert isinstance(channel_names, tuple)

        if data_length % FIT_SIZE_IN_BYTES != 0:
            raise PilusDeserializeError("Invalid chunk tRAN chunk length.")
        transition_count = data_length // FIT_SIZE_IN_BYTES

        # Make data structure
        mutable_site_data: dict[str, list[FitComplex]] = {}
        for channel_name in channel_names:
            mutable_site_data[channel_name] = []

        # Fill in data structure
        for _ in range(transition_count):
            time_start = read_double(io)
            time_end = read_double(io)
            for channel_name in channel_names:
                fit_complex = _fit_complex_from_io(
                    io, time_start=time_start, time_end=time_end
                )
                mutable_site_data[channel_name].append(fit_complex)

        # Freeze data structure
        site_data: SiteData = {
            channel_name: tuple(fits)
            for channel_name, fits in mutable_site_data.items()
        }
        return cls(site_data=site_data)


def _fit_complex_from_io(
    io: BinaryIO, *, time_start: float, time_end: float
) -> FitComplex:
    re = _transition_fit_from_io(io)
    im = _transition_fit_from_io(io)
    return FitComplex(re=re, im=im, time_start=time_start, time_end=time_end)


def _transition_fit_from_io(io: BinaryIO) -> TransitionFit:
    return TransitionFit(
        scale=read_double(io),
        center=read_double(io),
        width=read_double(io),
        baseline=read_double(io),
        offset=read_double(io),
        peak_height=read_double(io),
        transition_time=read_double(io),
        mse=read_double(io),
        noise=read_double(io),
        snr=read_double(io),
        ascend=read_double(io),
        iterations=read_int(io, 4),
        origin=read_int(io, 4),
    )
