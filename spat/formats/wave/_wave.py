import wave
from typing import BinaryIO

from .._errors import SpatError
from ._lpcm import Lpcm


class SpatWaveError(SpatError, wave.Error):
    """Raised if the WAVE deserializer fails."""


_ONE_SECOND_IN_NANOSECONDS = int(1e9)


def from_io(io: BinaryIO) -> Lpcm:
    """Deserialize IO stream into an instance of the given type."""
    ### Metadata
    # The actual deserialization happens at `Wave_read`. The subsequent calls to
    # `reader.get*` simply retrives the already-deserialized data. That's why the
    # `try..except` block is only around `Wave_read` itself.
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
    ### Data
    try:
        # `frames` is the logical number of samples
        frames = reader.getnframes()
        data = reader.readframes(frames)
    except wave.Error as exc:
        raise SpatWaveError(f'Could not deserialize WAVE data: "{exc}"') from exc
    # Wrap metadata and data into the given type
    return Lpcm(byte_depth, time_step_ns, data)


def to_io(lpcm: Lpcm, io: BinaryIO) -> None:
    """Serialize given type to the IO stream."""
    writer = wave.Wave_write(io)
    # Set metadata first
    writer.setnchannels(1)
    writer.setsampwidth(lpcm.byte_depth)
    writer.setframerate(1e9 // lpcm.time_step_ns)
    writer.setnframes(len(lpcm))
    # Write data and metadata. Yes, it writes both even though the method name
    # is `writeframesraw`. It's an error to change the metadata after this call.
    try:
        writer.writeframesraw(lpcm.data)
    except wave.Error as exc:
        raise SpatWaveError(f'Could not serialize data to WAVE: "{exc}"') from exc
