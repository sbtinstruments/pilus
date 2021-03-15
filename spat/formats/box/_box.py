import logging
from pathlib import Path
from typing import Dict
from zipfile import ZipFile

from ...types import Box, BoxItem
from .._utility import freeze_mapping
from ._errors import BoxError
from ._manifest import Manifest

_LOGGER = logging.getLogger(__name__)


_MANIFEST_PATH = Path("manifest.json")


def from_file(file: Path) -> Box:
    with ZipFile(file) as zf:
        pass


def from_dir(root: Path) -> Box:
    if not root.is_dir():
        raise BoxError(f'Given root "{root}" is not a directory')

    # Manifest
    manifest_path = root / _MANIFEST_PATH
    manifest = Manifest.from_path(manifest_path)

    # Items
    raw_items: Dict[Path, BoxItem] = {}
    files = (p for p in root.rglob("*") if p.is_file() and p != manifest_path)
    for file in files:
        ext = "".join(file.suffixes)
        try:
            media_type = manifest.ext_to_media_type[ext]
        except KeyError as exc:
            raise BoxError(f'Manifest does not mention file "{file}"') from exc
        with file.open("rb") as f:
            data = f.read()
        item = BoxItem(media_type, data)
        raw_items[file.relative_to(root)] = item

    items = freeze_mapping(raw_items)
    return Box(items)
