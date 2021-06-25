import logging
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

from ...types import Box, BoxValue
from .._parser_map import IdentifiedData, try_parse
from ._errors import BoxError
from ._manifest import Manifest

_LOGGER = logging.getLogger(__name__)


def from_file(file: Path) -> Box:
    with ZipFile(file) as zf:
        pass


def from_dir(root: Path, *, manifest: Optional[Manifest] = None) -> Box:
    # We define `manifest_path` inside the function because the current working
    # directory affects it's state.
    manifest_path = Path("manifest.json")
    if not root.is_dir():
        raise BoxError(f'Given root "{root}" is not a directory')
    children = set(c.relative_to(root) for c in root.iterdir())
    # Filter out the manifest file from the children
    children.remove(manifest_path)
    # Manifest
    if manifest is None:
        manifest = Manifest.from_file(root / manifest_path)
    # Items
    raw_items: dict[str, BoxValue] = {
        c.name: _resolve_child(c, manifest=manifest) for c in children
    }
    return Box(**raw_items)


def _resolve_child(child: Path, *, manifest: Manifest) -> BoxValue:
    # Recurse into sub-directory
    if child.is_dir():
        return from_dir(child, manifest=manifest)
    # Identify and parse file
    if child.is_file():
        identified = _identify_file(child, manifest=manifest)
        # Try to parse file
        return try_parse(identified)
    # Raise specific error on symlink
    if child.is_symlink():
        raise BoxError(f"We don't support symlinks: {child}")
    # Raise general error for all other child types
    raise BoxError(f"Unknown child: {child}")


def _identify_file(file: Path, *, manifest: Manifest) -> IdentifiedData:
    """Identify file using the manifest."""
    # First, try the path
    try:
        print("======================================")
        print(f"file={file}")
        media_type = manifest.path_to_media_type[file]
    except KeyError:
        pass
    # Second, try the extension
    ext = "".join(file.suffixes)
    try:
        media_type = manifest.extension_to_media_type[ext]
    except KeyError as exc:
        raise BoxError(f'Manifest does not mention file "{file}"') from exc
    # Read the data into memory
    with file.open("rb") as f:
        data = f.read()
    return IdentifiedData(media_type, data)
