from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterator

from immutables import Map

from ._item import SeedItem


@dataclass(frozen=True)
class Seed:
    _items: Map[Path, SeedItem] = field(default_factory=Map)

    def __getitem__(self, path: Path) -> SeedItem:
        return self._items[path]

    def __iter__(self) -> Iterator[Path]:
        return iter(self._items)


# @dataclass(frozen=True)
# class Seed:
#     """Immutable mapping for time-indexed raw binary data.

#     That was a mouthful. Let's take it one word at a time.

#     ### Immutable

#     You can't change a seed. All operations on a seed return a copy
#     with the changes. The original seed remains the same.

#     This means you can pass a seed around and not worry that someone
#     might change the seed while you're using it. This is especially
#     important in concurrent applications.

#     ### Mapping

#     We organize the data in a string-based a mapping.
#     Something like the following:

#       {
#         "humidity": Channel(...),
#         "temperature_sensor0": Channel(...),
#         "temperature_sensor1": Channel(...),
#         ...
#       }

#     We call the entries for "channels". In the example above,
#     "humidity" is the name of the first channel, "temperature_sensor1"
#     is the name of the second channel, and so forth.

#     ### Time-indexed

#     Each datum in a channel corresponds to an absolute point in time.
#     E.g., if the data is audio, each sample corresponds to the
#     point in time when we recorded it.

#     We require that the frequency (the spacing between each consecutive
#     time point) is constant. Furthermore, the frequency is the same
#     across all channels.

#     ### Raw binary data

#     We don't assume anything about the nature of data in a channel.
#     It could be audio, video, or something else entirely.

#     The data format must be raw, though. No sub-format, encoding,
#     compression, or the like. Just an array of audio samples, video
#     frames, or whatever suits the use case.

#     At a later point in time, we may loosen this requirement.


#     ## Examples

#     In practice, a seed is something like this:

#       {
#         "fc0_site0_lf_re": Channel(...),
#         "fc0_site0_lf_im": Channel(...),
#         "fc0_site0_hf_re": Channel(...),
#         "fc0_site0_hf_im": Channel(...),
#         "fc0_site1_lf_re": Channel(...),
#         ...,
#         "fc3_site1_hf_im": Channel(...),
#       }

#     This is similar to what you might find in an IQS file. A seed, however,
#     goes beyond the IQS specification. A seed allows arbitrary channels:

#       {
#         "fc0_site0_lf_convolutionA": Channel(...),
#         "fc0_site0_hf_convolutionA": Channel(...),
#         "fc0_site0_electrode1": Channel(...)
#       }

#     In other words, a seed is a representation for general-purpose
#     data. E.g., a seed can contain multitrack audio data:

#       {
#         "lead-vox": Channel(...),
#         "bass_amp1": Channel(...),
#         "bass_amp2": Channel(...),
#         "kick_in": Channel(...),
#         "kick_sample": Channel(...),
#         "kick_sub": Channel(...),
#         "snare_up1": Channel(...),
#         "snare_up2": Channel(...),
#         ...
#       }

#     ### Practical conventions

#     You may want to store a hierarchy within a seed. In this case,
#     agree on a delimiter and use this in the channel names to
#     separate different levels. E.g., the delimiter "__":

#       {
#         "fc0__site0__lf_re": Channel(...),
#         "fc0__site0__lf_im": Channel(...),
#         "fc0__site1__lf_re": Channel(...),
#         "fc0__site1__lf_im": Channel(...),
#         "fc1__site0__lf_re": Channel(...),
#         ...
#       }

#     Note that the seed itself is a single-level mapping. You're
#     responsible for any hierarchy/semantics that you build on top of
#     this. E.g., the seed won't guarantee that other users follow your
#     delimiter-based convention; that's your responsibility.
#     """

#     time_step_ns: int
#     start_time: datetime
#     _channels: ChannelMap

#     def __post_init__(self) -> None:
#         self._raise_if_heterogenous()

#     def _raise_if_heterogenous(self) -> None:
#         """Raise `ValueError` if the channels do not have the same length."""
#         lengths = (len(c) for c in self._channels.values())
#         if len(set(lengths)) > 1:
#             raise ValueError("All channels must be of the same length.")

#     def __getitem__(self, name: str) -> Channel:
#         return self._channels[name]


#     @classmethod
#     def save(cls,file_name: str) -> None:
#         """Save data to file."""
#         # Make sure pickle extension is added
#         if not file_name.endswith('.pkl'): file_name += '.pkl'
#         # Write file
#         with open(file_name, 'wb') as output:
#             # -1 means that the data is dumped using the Highest protocol
#             pickle.dump(cls, output, -1)

# def _tree_string(data:Union[dict,DefaultDict], level=0) -> str:
#     """String nested stucture overview."""
#     out_str = ""
#     for key, value in data.items():
#         out_str = out_str + "\n" + level*"  " + key
#         if isinstance(value,dict):
#             out_str = out_str + ":"
#             out_str = out_str + _tree_string(value,level=level+1)
#     return out_str


# def load(file_name:str) -> Seed:
#     """Load data from file."""
#     with open(file_name, 'rb') as input:
#         seed = pickle.load(input)

#     return seed
