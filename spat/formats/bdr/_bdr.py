from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, BinaryIO, Optional, Union
from ._errors import BdrError
from ._signature import read_and_validate_signature
from ._chunks._chunk import AhdrChunk, read_chunk
from ._chunks._tran import TranChunk, tRAN_segment
from ._chunks._chunk import DataChunk, NotImplementedChunk



@dataclass(frozen=True)
class Bdr:
    """Serialized BDR chunks.
    
    .tran contains the tRAN chunk data for all channels
    .time contains the corresponding time_range data
    """

    tran: dict[str, list[tRAN_segment]]
    time: list[dict[str, int]]


def from_io(io: BinaryIO) -> Optional[Bdr]:
    """Deserialize IO stream into a BDR instance."""
    # Signature
    read_and_validate_signature(io)
    header: Optional[AhdrChunk] = None
    data: list[TranChunk] = list()

    while chunk := read_chunk(io, header=header):
        if isinstance(chunk, AhdrChunk):
            header = chunk
        # Store all data chunks
        if isinstance(chunk, TranChunk):
            data.append(chunk)
        # We cover all chunk types, sd we should not hit this `else`
        else:
            pass
    # The BDR file contained no data
    if header is None or not data:
        return None

    # Merge all data together
    merged_data = TranChunk.merge_all(*data)
    return Bdr(*merged_data)
