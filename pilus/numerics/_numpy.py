import numpy as np

from pilus.formats.iqs import IqsAggregate


def iqs_to_numpy_array(
    iqs: IqsAggregate,
    site_order=["site0", "site1"],
    channel_order=["lf", "hf"],
    component_order=["re", "im"],
) -> np.ndarray:
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


def iqs_timestamp_array(iqs: IqsAggregate, site="site0", channel="lf"):
    duration_s = iqs.duration_ns * 1e-9
    total_logical_length = iqs.duration_ns // iqs.sites[site][channel].time_step_ns
    time_step_s = duration_s / total_logical_length
    return np.arange(0, duration_s, time_step_s)
