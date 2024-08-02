from __future__ import annotations

from dataclasses import dataclass

from ...forge import FORGE
from ._lpcm import Lpcm
from ._wave_meta import WaveMeta


@dataclass(frozen=True)
class Wave:
    """Linear, pulse-code-modulated (LPCM) signal stored in memmory."""

    lpcm: Lpcm
    metadata: WaveMeta

    @classmethod
    def from_lpcm_and_metadata(cls, lpcm: Lpcm, metadata: WaveMeta) -> Wave:
        """Create instance from LPCM and metadata."""
        return cls(lpcm, metadata)


FORGE.register_combiner(Wave.from_lpcm_and_metadata)
