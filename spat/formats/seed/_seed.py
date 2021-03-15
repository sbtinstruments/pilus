from pathlib import Path
from typing import Dict

from ...types import Extrema, Seed, SeedItem
from .. import box as box_format
from .. import extrema_json
from .._utility import freeze_mapping
from ._errors import SeedError

# _EXT_TO_MEDIA_TYPE: Dict[str, str] = {
#     ".wav": "audio/vnd.wave",
#     ".wav-meta.json": "application/vnd.sbt.wav-meta+json",
#     ".extrema.json": "application/vnd.sbt.extrema+json",
#     ".transitions.json": "application/vnd.sbt.transitions+json",
#     ".alg.json": "application/vnd.sbt.alg+json",
# }

_PARSERS = {"application/vnd.sbt.extrema+json": extrema_json.from_data}


def from_dir(root: Path) -> Seed:
    try:
        box = box_format.from_dir(root)
    except box_format.BoxError as exc:
        raise SeedError(f"Could not read box format: {str(exc)}") from exc

    raw_items: Dict[Path, SeedItem] = {}
    for path, item in box.items():
        try:
            parser = _PARSERS[item.media_type]
        except KeyError as exc:
            raise SeedError(f'Unknown media type "{item.media_type}"') from exc
        raw_items[path] = parser(item.data)

    items = freeze_mapping(raw_items)
    return Seed(items)
