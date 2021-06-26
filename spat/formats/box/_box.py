import logging
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

from ...types import Box, BoxValue
from .._parser_map import IdentifiedData, try_parse
from ._errors import BoxError
from ._manifest import Manifest

_LOGGER = logging.getLogger(__name__)


_MANIFEST_PATH = Path("manifest.json")


def from_file(file: Path) -> Box:
    with ZipFile(file) as zf:
        pass


def from_dir(
    directory: Path,
    *,
    root: Optional[Path] = None,
    manifest: Optional[Manifest] = None,
) -> Box:
    if root is None:
        root = directory
    if not directory.is_dir():
        raise BoxError(f'"{directory}" is not a directory')
    children = set(directory.iterdir())
    # Manifest
    if manifest is None:
        manifest_path = root / _MANIFEST_PATH
        manifest = Manifest.from_file(manifest_path)
        # Filter out the manifest file from the children
        children.remove(manifest_path)
    # Resolve the children in the directory
    resolved_children: dict[str, BoxValue] = {
        c.name: _resolve_child(c, root=root, manifest=manifest) for c in children
    }
    return Box(**resolved_children)


def _resolve_child(child: Path, *, root: Path, manifest: Manifest) -> BoxValue:
    # Recurse into sub-directory
    if child.is_dir():
        return from_dir(child, root=root, manifest=manifest)
    # Identify and parse file
    if child.is_file():
        identified = _identify_file(child, root=root, manifest=manifest)
        # Try to parse file
        return try_parse(identified)
    # Raise specific error on symlink
    if child.is_symlink():
        raise BoxError(f"We don't support symlinks: {child}")
    # Raise general error for all other child types
    raise BoxError(f"Unknown child: {child}")


def _identify_file(file: Path, *, root: Path, manifest: Manifest) -> IdentifiedData:
    """Identify file using the manifest."""
    media_type = _get_media_type(file, root=root, manifest=manifest)
    # Read the data into memory
    with file.open("rb") as f:
        data = f.read()
    return IdentifiedData(media_type, data)


def _get_media_type(file: Path, *, root: Path, manifest: Manifest) -> str:
    # First, try the path
    relative_path = file.relative_to(root)
    try:
        return manifest.path_to_media_type[relative_path]
    except KeyError:
        pass
    # Second, try the extension
    ext = "".join(file.suffixes)
    try:
        return manifest.extension_to_media_type[ext]
    except KeyError as exc:
        raise BoxError(f'Manifest does not mention file "{file}"') from exc
