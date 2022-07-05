from __future__ import annotations

from dataclasses import dataclass

from ..formats import wave
from ..formats.registry import add_deserializer, add_merger
from ._wave_meta import WaveMeta


@dataclass(frozen=True)
class Wave:
    """Linear, pulse-code-modulated (LPCM) signal stored in memmory."""

    lpcm: wave.Lpcm
    metadata: WaveMeta

    @classmethod
    def from_lpcm_and_metadata(cls, lpcm: wave.Lpcm, metadata: WaveMeta) -> Wave:
        """Create instance from LPCM and metadata."""
        return cls(lpcm, metadata)


add_deserializer("audio/vnd.wave", from_io=wave.from_io)
add_merger(Wave.from_lpcm_and_metadata)
