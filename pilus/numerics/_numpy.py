import numpy as np
import numpy.typing as npt

from pilus.formats.iqs import IqsAggregate


def iqs_to_numpy_array(
    iqs: IqsAggregate,
    site_order: tuple[str, ...] = ("site0", "site1"),
    channel_order: tuple[str, ...] = ("lf", "hf"),
    component_order: tuple[str, ...] = ("re", "im"),
) -> npt.NDArray[np.float64]:
    """Convert the given IQS aggregate to a multi-dimensional array."""
    # Allocate array
    total_logical_length = iqs.duration_ns // iqs.sites["site0"]["lf"].time_step_ns
    array = np.empty([2, 2, 2, total_logical_length], dtype=np.float64)
    for sitenum, site in enumerate(site_order):
        for channelnum, channel in enumerate(channel_order):
            for componentnum, component in enumerate(component_order):
                channel_data = iqs.sites[site][channel]
                max_amplitude = iqs.sites[site][channel].max_amplitude
                array[sitenum, channelnum, componentnum, :] = (
                    np.frombuffer(getattr(channel_data, component), dtype=np.int32)
                    / max_amplitude
                )
    return array


def iqs_timestamp_array(
    iqs: IqsAggregate, site: str = "site0", channel: str = "lf"
) -> npt.NDArray[np.float64]:
    """Return a timestamp array that corresponds to the given IQS aggregate."""
    duration_s = iqs.duration_ns * 1e-9
    total_logical_length = iqs.duration_ns // iqs.sites[site][channel].time_step_ns
    time_step_s = duration_s / total_logical_length
    return np.arange(0, duration_s, time_step_s)


# keys = [
#     "site",
#     "transition_time",
#     "hfre_scale",
#     "hfim_scale",
#     "lfre_scale",
#     "lfim_scale",
#     "hf_phase",
#     "lf_phase",
#     "hf_amp",
#     "lf_amp",
#     "hfre_width",
#     "hfim_width",
#     "lfre_width",
#     "lfim_width",
#     "center",
# ]
# import numpy as np
# def serialize(chunks):
#     "It serialize the data so it is more accesible to data analysts"
#     data = {i: [] for i in Bdr.keys}
#     for ch in chunks:
#         site = ch.header.site_name
#         time_start = ch.header.time_start * 1e-6
#         for d in ch.data:
#             for k in d.keys():
#                 data[k + "_scale"].append(d[k].scale)
#                 data[k + "_width"].append(d[k].width)
#             data["site"].append(site)
#             data["transition_time"].append(d[k].transition_time)
#             data["center"].append(d[k].center)
#         if ch == chunks[-1]:
#             time_end = ch.header.time_end * 1e-6

#     for k in ["hf", "lf"]:
#         data[k + "_phase"] = np.arctan2(data[k + "im_scale"], data[k + "re_scale"])
#         data[k + "_amp"] = np.sqrt(
#             np.square(data[k + "re_scale"]) + np.square(data[k + "im_scale"])
#         )

#     for k in data.keys():
#         if not isinstance(data[k], np.ndarray):
#             data[k] = np.array(data[k])
#     return chunks, data, time_start, time_end
