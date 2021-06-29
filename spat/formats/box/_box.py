import logging
from enum import Enum, unique
from pathlib import Path
from typing import Any, Optional

# We explicitly import the `_map` file to get the proper typing (corresponding to the
# `_map.pyi` file).
from immutables import Map

from ..registry import IdentifiedResource, Resource, SpatNoParserError, parse
from ._errors import BoxError
from ._manifest import Manifest

# from zipfile import ZipFile


_LOGGER = logging.getLogger(__name__)
_MANIFEST_PATH = Path("manifest.json")

Box = Map[str, Any]


@unique
class MissingParserPolicy(Enum):
    """What to do when there is no parser for a media type."""

    STORE_DATA = "store-data"
    STORE_METADATA = "store-metadata"


# TODO: Add a ZIP-based loader
# def from_file(file: Path) -> Box:
#     with ZipFile(file) as zf:
#         pass


def from_dir(
    directory: Path,
    *,
    missing_parser_policy: Optional[MissingParserPolicy] = None,
    root: Optional[Path] = None,
    manifest: Optional[Manifest] = None,
) -> Box:
    """Return box based on the directory.

    Automatically parses the files in the directory based on the currently registered
    parsers.
    """
    # Default arguments
    if missing_parser_policy is None:
        missing_parser_policy = MissingParserPolicy.STORE_METADATA
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
    resolved_children: dict[str, Any] = {
        c.name: _resolve_child(
            c,
            missing_parser_policy=missing_parser_policy,
            root=root,
            manifest=manifest,
        )
        for c in children
    }
    return Box(**resolved_children)


def _resolve_child(
    child: Path,
    **kwargs: Any,
) -> Any:
    # Recurse into sub-directory
    if child.is_dir():
        return from_dir(child, **kwargs)
    # Identify and parse file
    if child.is_file():
        return _identify_and_parse_file(child, **kwargs)
    # Raise specific error on symlink
    if child.is_symlink():
        raise BoxError(f"We don't support symlinks: {child}")
    # Raise general error for all other child types
    raise BoxError(f"Unknown child: {child}")


def _identify_and_parse_file(
    file: Path,
    *,
    missing_parser_policy: MissingParserPolicy,
    root: Path,
    manifest: Manifest,
) -> Any:
    """Identify file type using the manifest."""
    media_type = _get_media_type(file, root=root, manifest=manifest)
    try:
        return parse(media_type, file)
    except SpatNoParserError:
        resource: Resource
        if missing_parser_policy is MissingParserPolicy.STORE_DATA:
            resource = file.read_bytes()
        elif missing_parser_policy is MissingParserPolicy.STORE_METADATA:
            resource = file
        else:
            # We cover all `MissingParserPolicy` values
            assert False
        return IdentifiedResource(media_type, resource)


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
