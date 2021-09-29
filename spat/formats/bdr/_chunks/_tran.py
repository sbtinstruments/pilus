from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, TYPE_CHECKING, BinaryIO, ClassVar, Union
from itertools import product

from ._ahdr import AhdrChunk
from .._errors import BdrError

from ...iqs._io_utilities import read_int, read_double

CHANNELS = ["".join(i) for i in list(product(*[["hf", "lf"], ["im", "re"]]))]


@dataclass(frozen=True)
class tRAN_segment:
    """Single chunk part tRAN chunk"""

    scale: float
    center: float
    width: float
    baseline: float
    offset: float
    peak_height: float
    # 2*offset
    transition_time: float
    mse: float
    noise: float
    snr: float
    ascend: float
    iterations: int
    origin: int
    name: Optional[str] = None

    @classmethod
    def from_io(cls, io: BinaryIO, name: Optional[str]) -> tRAN_segment:
        """Read tRAN chunk segment.

        See baxter/formats/bdr/_bdr.py, baxter/formats/bdr/_alg_ctypes.py
        """
        data = {}
        # scale[ctypes.c_double]
        data["scale"] = read_double(io)
        # center[ctypes.c_double]
        data["center"] = read_double(io)
        # width[ctypes.c_double]
        data["width"] = read_double(io)
        # baseline[ctypes.c_double]
        data["baseline"] = read_double(io)
        # offset[ctypes.c_double]
        data["offset"] = read_double(io)
        # peak_height[ctypes.c_double]
        data["peak_height"] = read_double(io)
        # transition_time[ctypes.c_double]
        data["transition_time"] = read_double(io)
        # mse[ctypes.c_double]
        data["mse"] = read_double(io)
        # noise[ctypes.c_double]
        data["noise"] = read_double(io)
        # snr[ctypes.c_double]
        data["snr"] = read_double(io)
        # ascend[ctypes.c_double] Marcos: make up just to add up 400 bytes chunk length
        data["ascend"] = read_double(io)
        # iterations[ctypes.int]
        data["iterations"] = read_int(io, 4)
        # origin[ctypes.int]
        data["origin"] = read_int(io, 4)
        return cls(**data, name=name)


@dataclass(frozen=True)
class TranChunk:
    """Used to interpret the subsequent tRAN chunks."""

    type_: ClassVar[bytes] = b"tRAN"
    data: list[dict[str, tRAN_segment]]
    time_range: list[dict[str, int]]

    @classmethod
    def from_io(cls, io: BinaryIO, chunk_length: int, header: AhdrChunk) -> TranChunk:
        """Deserialize the IO stream into a tRAN chunk.

        May raise `IqsError` or one of its derivatives.
        """
        if chunk_length % 400 != 0:
            raise BdrError("Invalid chunk tRAN chunk length.")
        n_trans = chunk_length // 400
        data = []
        data_time = []
        # There are ```(length) mod 400``` chunk segments in the chunk.
        # A chunk segment looks like the following:
        # { start_time,
        #   end_time,
        #   4TPS chunks {
        #       'hfre'
        #       'hfim'
        #       'lfre'
        #       'lfim'
        #     },
        # }
        for i in range(n_trans):
            # start time
            time_start = read_double(io)
            # end time
            time_end = read_double(io)
            FIT4: dict[str, tRAN_segment] = {}
            _ax = ["re", "im"]
            for chnl in header.channel_name:
                for ax in _ax:
                    FIT4[chnl + ax] = tRAN_segment.from_io(io, chnl + "_" + ax)

            data_time.append({"time_start": time_start, "time_end": time_end})
            data.append(FIT4)

        return cls(data=data, time_range=data_time)

    @classmethod
    def merge_all(
        cls, *chunks: TranChunk
    ) -> tuple[dict[str, list[tRAN_segment]], list[dict[str, int]]]:
        # Early out if there are no chunks
        if not chunks:
            raise ValueError("Can't merge empty sequence of chunks")
        first_chunk = chunks[0]
        try:
            chnl_names = list(first_chunk.data[0].keys())
        except IndexError:
            raise ValueError("Could not merge empty data chunks")

        merged: dict[str, list[tRAN_segment]] = {k: [] for k in chnl_names}
        time_range: list[dict[str, int]] = []

        # Merge chunks into lists
        for chunk in chunks:
            # TranChunk
            time_range = time_range + chunk.time_range
            for seg in chunk.data:
                for k, v in seg.items():
                    merged[k].append(v)

        return merged, time_range
