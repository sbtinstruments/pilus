from dataclasses import dataclass
from enum import Enum, auto
from typing import BinaryIO, Optional, Union
from itertools import product
from ._errors import BdrError
from ._signature import read_and_validate_signature
from ._chunks._chunk import AhdrChunk, read_chunk
from ._chunks._tran import TranChunk
from ._chunks._chunk import DataChunk, NotImplementedChunk

CHANNELS = ["".join(i) for i in list(product(*[['hf','lf'],['im','re']]))]

#NOTE: there are a lot of different chunks in BDR, This reads only the tRAN
# (transition fits) chunks

@dataclass(frozen=True)
class Bdr:
    """Raw BDR chunks."""
    data: list[DataChunk]

def from_io(
    io: BinaryIO) -> Optional[Bdr]:
    """Deserialize IO stream into a BDR instance.
    """
    # Signature
    read_and_validate_signature(io)
    header: Optional[AhdrChunk] = None
    data: list[DataChunk] = list()

    while chunk := read_chunk(io, header=header):
        if isinstance(chunk, AhdrChunk):
            header = chunk
        # Store all data chunks
        if isinstance(chunk, TranChunk):
            data.append(chunk)
        # elif isinstance(chunk,NotImplementedChunk):
        #     # Discard all unidentified ancilliary (non-critical) chunks
        #     pass
        # We cover all chunk types, sd we should not hit this `else`
        else:
            pass
            # print()
            # assert False
    # The BDR file contained no data
    if header is None or not data:
        return None
    
    #TODO: below
    # trans = (
    #     _ensure_idat(chunk, site_name=version_1_0_0_site_name, header=header)
    #     for chunk in data
    # )
    # # Merge all data together
    # merged_transition = IdatChunk.merge_all(*trans)
    return Bdr(data)
