from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, BinaryIO, Optional, Union
from ._errors import BdrError
from ._signature import read_and_validate_signature
from ._chunks._chunk import AhdrChunk, read_chunk
from ._chunks._tran import TranChunk, tRAN_segment
from ._chunks._chunk import DataChunk, NotImplementedChunk

import numpy as np


@dataclass(frozen=False)
class Bdr:
    """Contains the list of chunks present on a BDR file."""

    keys = [
        "site",
        "transition_time",
        "hfre_scale",
        "hfim_scale",
        "lfre_scale",
        "lfim_scale",
        "hf_phase",
        "lf_phase",
        "hf_amp",
        "lf_amp",
        "hfre_width",
        "hfim_width",
        "lfre_width",
        "lfim_width",
        "center",
    ]
    chunks: list[TranChunk]
    data: dict[str, np.ndarray]
    time_start: float
    time_end: float

    @classmethod
    def from_io(cls, io: BinaryIO):
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
        inp = serialize(data)
        return cls(*inp)


def serialize(chunks):
    "It serialize the data so it is more accesible to data analysts"
    data = {i: [] for i in Bdr.keys}
    for ch in chunks:
        site = ch.header.site_name
        time_start = ch.header.time_start * 1e-6
        for d in ch.data:
            for k in d.keys():
                data[k + "_scale"].append(d[k].scale)
                data[k + "_width"].append(d[k].width)
            data["site"].append(site)
            data["transition_time"].append(d[k].transition_time)
            data["center"].append(d[k].center)
        if ch == chunks[-1]:
            time_end = ch.header.time_end * 1e-6

    for k in ["hf", "lf"]:
        data[k + "_phase"] = np.arctan2(data[k + "im_scale"], data[k + "re_scale"])
        data[k + "_amp"] = np.sqrt(
            np.square(data[k + "re_scale"]) + np.square(data[k + "im_scale"])
        )

    for k in data.keys():
        if not isinstance(data[k], np.ndarray):
            data[k] = np.array(data[k])
    return chunks, data, time_start, time_end
