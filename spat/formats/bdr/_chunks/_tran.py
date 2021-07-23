from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING, BinaryIO, ClassVar, Union
from ._ahdr import AhdrChunk
from .._errors import BdrError

from ...iqs._io_utilities import (
    read_int,
    read_exactly
)

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
    iterations: int
    origin: int
    name: Optional[str] = None

    @classmethod
    def from_io(cls, io:BinaryIO, name:Optional[str]) -> tRAN_segment:
        """ Read tRAN chunk segment.
        
        See baxter/formats/bdr/_bdr.py, baxter/formats/bdr/_alg_ctypes.py
        """
        data = {}
        # scale[ctypes.c_double]
        data["scale"] = read_int(io, 8)
        # center[ctypes.c_double]
        data["center"] = read_int(io, 8)
        # width[ctypes.c_double]
        data["width"] = read_int(io, 8)
        # baseline[ctypes.c_double]
        data["baseline"] = read_int(io, 8)
        # offset[ctypes.c_double]
        data["offset"] = read_int(io, 8)
        # peak_height[ctypes.c_double]
        data["peak_height"] = read_int(io, 8)
        # transition_time[ctypes.c_double]
        data["transition_time"] = read_int(io, 8)
        # mse[ctypes.c_double]
        data["mse"] = read_int(io, 8)
        # noise[ctypes.c_double]
        data["noise"] = read_int(io, 8)
        # snr[ctypes.c_double]
        data["snr"] = read_int(io, 8)
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
    def from_io(cls, io: BinaryIO, chunk_length:int , header: AhdrChunk) -> TranChunk:
        """Deserialize the IO stream into a tRAN chunk.

        May raise `IqsError` or one of its derivatives.
        """
        if chunk_length % 400 != 0:
            raise BdrError("Invalid chunk tRAN chunk length.")
        n_trans = chunk_length // 400
        data = []
        data_time = []
        for i in range(n_trans):
        # There are ```(length) mod 400``` chunk pieces in the chunk. 
        # A chunk piece looks like the following:
        # { start_time,
        #   end_time,
        #   4 TPS chunks {
        #    'hf_re'
        #    'hf_im'
        #    'lf_re'
        #    'lf_im'
        #     },
        # }
        # start time
            time_start = read_int(io, 8)
            # end time
            time_end = read_int(io, 8)
            FIT4:dict[str,tRAN_segment] = {}
            _ax = ['re','im']
            for chnl in header.channel_name:
                for ax in _ax:
                    FIT4[chnl+ax] = tRAN_segment.from_io(io, chnl + "_" + ax)

            data_time.append({"time_start": time_start, "time_end": time_end})
            data.append(FIT4)
            
        return cls(data=data, time_range=data_time)


    #############
    #     number_of_sites = read_int(io, 4)
    #     sites: dict[str, SiteHeader] = dict()
    #     for _ in range(number_of_sites):
    #         site_name = read_terminated_string(io, 256)  # E.g.: "site0"
    #         number_of_channels = read_int(io, 4)
    #         site_header: SiteHeader = dict()
    #         for _ in range(number_of_channels):
    #             channel_name = read_terminated_string(io, 256)  # E.g.: "hf"
    #             time_step_ns = read_int(io, 4)
    #             byte_depth = read_int(io, 1)
    #             # Yes, this is actually a 64-byte integer (not a 64-bit integer).
    #             # This is by design since byte depth theoretically goes to 64
    #             # (though it's usually only 4).
    #             max_amplitude = read_int(io, 64, signed=True)
    #             # Add channel header to site header
    #             channel_header = ChannelHeader(time_step_ns, byte_depth, max_amplitude)
    #             site_header[channel_name] = channel_header
    #         # Add site header to chunk
    #         sites[site_name] = site_header
    #     return cls(sites)
