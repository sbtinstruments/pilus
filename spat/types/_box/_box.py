from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Tuple

from immutables import Map
from immutables.map import MapValues

from ._item import BoxItem

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

"""
  ## Container

  media type: application/vnd.sbt.container+zip

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

  /settings/production.alg.json
  /settings/tuned-for-bacillus.alg.json
  /data/site0/hf/re/part0.wav
  /data/site0/hf/re/part0.wav-meta.json
  /data/site0/hf/re/part0--production.extrema.json
  /data/site0/hf/re/part0--production.transitions.json
  /data/site0/hf/re/part0--tuned-for-bacillus.extrema.json
  /data/site0/hf/re/part0--tuned-for-bacillus.transitions.json
  /data/site0/hf/re/part1.wav
  /data/site0/hf/re/part1.wav-meta.json
  /data/site0/hf/re/combined--production.extrema.json
  /data/site0/hf/re/combined--production.transitions.json

"""


@dataclass(frozen=True)
class Box:
    _items: Map[Path, BoxItem] = field(default_factory=Map)

    def __getitem__(self, path: Path) -> BoxItem:
        return self._items[path]

    def __iter__(self) -> Iterator[Path]:
        return iter(self._items)

    def values(self) -> Iterable[BoxItem]:
        return self._items.values()

    def items(self) -> Iterable[Tuple[Path, BoxItem]]:
        return self._items.items()
