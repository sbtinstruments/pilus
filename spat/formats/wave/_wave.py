import wave
from typing import BinaryIO, Protocol, Type, TypeVar

from .._errors import SpatError


class _InitProtocol(Protocol):  # pylint: disable=too-few-public-methods
    def __init__(  # pylint: disable=super-init-not-called
        self, __byte_depth: int, __time_step_ns: int, __data: bytes
    ) -> None:
        ...


T = TypeVar("T", bound=_InitProtocol)


class SpatWaveError(SpatError, wave.Error):
    """Raised if the WAVE deserializer fails."""


_ONE_SECOND_IN_NANOSECONDS = int(1e9)


def from_io(type_: Type[T], io: BinaryIO) -> T:
    """Construct instance of the given type based on a binary IO stream."""
    # Metadata
    try:
        reader = wave.Wave_read(io)
    except wave.Error as exc:
        raise SpatWaveError(f'Could not deserialize WAVE metadata: "{exc}"') from exc
    byte_depth = reader.getsampwidth()
    # Check number of channels
    channels = reader.getnchannels()
    if channels != 1:
        raise SpatWaveError(
            f"Found {channels} channels. "
            "We only support single-channel (mono) WAVE data."
        )
    # Check frequency
    frequency_hz = reader.getframerate()
    time_step_ns = _ONE_SECOND_IN_NANOSECONDS // frequency_hz
    frequency_converted_back = _ONE_SECOND_IN_NANOSECONDS // time_step_ns
    frequency_delta = abs(frequency_converted_back - frequency_hz)
    if frequency_delta > 1:  # We allow 1 Hz of precision loss
        raise SpatWaveError(
            f"Found frequency of {frequency_hz} Hz. "
            "We can't convert this frequency to a time step in nanoseconds "
            f"without losing {frequency_delta} Hz of precision."
        )
    # Data
    try:
        # `frames` is the logical number of samples
        frames = reader.getnframes()
        data = reader.readframes(frames)
    except wave.Error as exc:
        raise SpatWaveError(f'Could not deserialize WAVE data: "{exc}"') from exc
    # Wrap metadata and data into the given type
    # TODO: TESTING
    data = bytes()
    return type_(byte_depth, time_step_ns, data)
