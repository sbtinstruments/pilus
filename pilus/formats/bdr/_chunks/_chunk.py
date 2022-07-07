from typing import Union

from ._misc import BlinChunk, ExtrChunk, NoisChunk, OdatChunk, PcexChunk, RtraChunk

NotImplementedChunk = Union[
    OdatChunk,
    NoisChunk,
    ExtrChunk,
    PcexChunk,
    BlinChunk,
    RtraChunk,
]
