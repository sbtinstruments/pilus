from functools import reduce
from typing import Any, Iterable, Optional, Type, TypeVar

from tinydb import TinyDB, where
from tinydb.queries import Query, QueryInstance
from tinydb.storages import MemoryStorage
from typeguard import check_type

from ._snip_attribute_declaration_map import SnipAttributeDeclarationMap
from ._snip_attributes import SnipAttribute
from ._snip_part import SnipPart
from ._snip_part_metadata import SnipAttributeMap, SnipPartMetadata

T = TypeVar("T")


class Snip:
    """Immutable, in-memory database.

    Common media type:     application/vnd.sbt.snip+zip
    Common file extension: .snip.zip

    /manifest.json
    {
        "extensionToMediaType": {
        ".wav": "audio/vnd.wave",
        ".wav-meta.json": "application/vnd.sbt.wav-meta+json",
        ".extrema.json": "application/vnd.sbt.extrema+json",
        ".transitions.json": "application/vnd.sbt.transitions+json",
        ".alg.json": "application/vnd.sbt.alg+json",
        }
    }

    /attributes.json
    {
        "enums": {
            "site": {
                "values": ["site0", "site1"]
            },
            "frequency": {
                "values": ["hf", "lf"]
            },
            "part": {
                "values": ["real", "imaginary"]
            },
            "settings": {
                "values": ["production", "tuned-for-bacillus"]
            }
        }
    }

    ### /data/{name}--{attr0}--{attr1}--{attr2}.{type}

    /data/settings--general.alg.json
    /data/settings--tuned-for-bacillus.alg.json
    /data/diff--site0--hf--re.wav
    /data/diff--site0--hf--re.wav-meta.json
    /data/diff--site0--hf--re--general.extrema.json
    /data/diff--site0--hf--re--general.transitions.json
    /data/diff--site0--hf--re--tuned-for-bacillus.extrema.json
    /data/diff--site0--hf--re--tuned-for-bacillus.transitions.json
    /data/diff--site0--hf--im.wav
    /data/diff--site0--hf--im.wav-meta.json
    ...
    /data/diff--site1--lf--im--tuned-for-bacillus.transitions.json

    """

    def __init__(
        self,
        parts: Iterable[SnipPart[Any]],
        attribute_declaration: SnipAttributeDeclarationMap,
    ) -> None:
        self._db = TinyDB(storage=MemoryStorage)
        documents = (
            {
                "value": part.value,
                "name": part.metadata.name,
                "attributes": part.metadata.attributes,
            }
            for part in parts
        )
        self._parts = self._db.table("part")
        self._parts.insert_multiple(documents)
        self._attribute_declaration = attribute_declaration

    def get(
        self,
        type_: Optional[Type[T]] = None,
        name: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Optional[SnipPart[T]]:
        query = self._args_to_query(type_, name, *args, **kwargs)
        document = self._parts.get(query)
        if document is None:
            return None
        return _doc_to_part(document)

    def search(
        self,
        type_: Optional[Type[T]] = None,
        name: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Iterable[SnipPart[T]]:
        query = self._args_to_query(type_, name, *args, **kwargs)
        documents = self._parts.search(query)
        return (_doc_to_part(doc) for doc in documents)

    def _args_to_query(
        self,
        type_: Optional[type] = None,
        name: Optional[str] = None,
        **kwargs: str,
    ) -> QueryInstance:
        AttributeNameAndValues = frozenset[tuple[str, SnipAttribute]]
        attributes: Optional[AttributeNameAndValues] = None
        # Consider all keyword arguments as attribute filters
        if kwargs:
            attributes = frozenset(self._attribute_declaration.parse_kwargs(**kwargs))
        # Convert argument to queries
        queries: list[QueryInstance] = []
        if type_ is not None:

            def _test_type(value: Any) -> bool:
                try:
                    check_type("value", value, type_)
                except TypeError:
                    return False
                return True

            queries.append(where("value").test(_test_type))
        if name is not None:
            queries.append(where("name") == name)
        if attributes is not None:

            def _test_attributes(value: SnipAttributeMap) -> bool:
                assert attributes is not None
                name_and_values: AttributeNameAndValues = frozenset(value.items())
                return name_and_values.issuperset(attributes)

            queries.append(where("attributes").test(_test_attributes))
        # Raise error if there are no queries
        if not queries:
            raise ValueError("You must provide at least one argument")
        # Combine all queries into one
        query = reduce(Query.__and__, queries)
        return query

    def __iter__(self) -> Iterable[SnipPart[Any]]:
        return (_doc_to_part(doc) for doc in self._parts)


def _doc_to_part(document: dict[str, Any]) -> SnipPart[Any]:
    value = document["value"]
    metadata = SnipPartMetadata(
        name=document["name"], attributes=document["attributes"]
    )
    return SnipPart(value=value, metadata=metadata)


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


"""
  ## Raw data

  E.g., the data in an IQS file.

  We split raw data into two files:
    1. LPCM data in WAVE format.
       my-data.wav
    2. Metadata. (data that doesn't fit into the WAVE file itself)
       my-data.wav-meta.json

  ### LPCM (Linear Pulse-Code Modulation) data

  Store main data in a WAVE file

  Media type: audio/vnd.wave
  Contains:
    * sample_rate: int
    * byte_depth: int
    * data: bytes

  ### Metadata

  Store metadata in a JSON file.

  Media type: application/vnd.sbt.wav-meta+json
  Contains: {
    "startTime": time point (absolute; UTC)
    "maxValue": max value of PCM data
  }

  ## Extrema

  Store extrema in an array in a JSON file.

  Media type: application/vnd.sbt.extrema+json
  Contains: [
    {
      "type": "minimum",
      "time": UTC in microseconds,
      "value": floating-point value relative to the baseline,
    },
    ...
  ]

  ## Transitions

  Store transitions in an array in a JSON file.

  Media type: application/vnd.sbt.transitions+json
  Contains: [
    {
      "model": {
        "name": "double-gaussian",
        "parameters": {
          "center": time point in microseconds (UTC),
          "scale": real value,
          "width": real value,
          "offset": time duration
        }
      }
    },
    ...
  ]

"""
