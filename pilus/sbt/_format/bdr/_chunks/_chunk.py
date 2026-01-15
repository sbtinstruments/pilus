from ._misc import BlinChunk, ExtrChunk, NoisChunk, OdatChunk, PcexChunk, RtraChunk

NotImplementedChunk = (
    OdatChunk | NoisChunk | ExtrChunk | PcexChunk | BlinChunk | RtraChunk
)
