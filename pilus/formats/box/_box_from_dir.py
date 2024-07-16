import logging
from enum import Enum, unique
from os import PathLike
from pathlib import Path
from typing import Annotated, Any, Optional

# from zipfile import ZipFile
from ..._magic import Medium, MediumSpec, detect_media_type
from ...basic import Box
from ...errors import PilusDeserializeError, PilusMissingMorpherError
from ...forge import FORGE
from ._manifest import Manifest

_LOGGER = logging.getLogger(__name__)
_MANIFEST_PATH = Path("manifest.json")


@unique
class MissingDeserializerPolicy(Enum):
    """What to do when there is no deserializer for a media type."""

    STORE_DATA = "store-data"
    STORE_METADATA = "store-metadata"


# TODO: Add a ZIP-based loader
# def from_file(file: Path) -> Box:
#     with ZipFile(file) as zf:
#         pass


@FORGE.register_deserializer
def from_dir(
    directory: Annotated[Path, "application/vnd.sbt.box"],
    *,
    missing_deserializer_policy: Optional[MissingDeserializerPolicy] = None,
    root: Optional[Path] = None,
    manifest: Optional[Manifest] = None,
) -> Box:
    """Return box based on the directory.

    Automatically deserializes the files in the directory based on the
    deserializers in the global registry.
    """
    # Default arguments
    if missing_deserializer_policy is None:
        missing_deserializer_policy = MissingDeserializerPolicy.STORE_METADATA
    if root is None:
        root = directory
    if not directory.is_dir():
        raise PilusDeserializeError(f'"{directory}" is not a directory')
    children = set(directory.iterdir())
    # Manifest
    if manifest is None:
        manifest_path = root / _MANIFEST_PATH
        manifest_data = manifest_path.read_text(encoding="utf8")
        manifest = Manifest.model_validate_json(manifest_data)
        # Filter out the manifest file from the children
        children.remove(manifest_path)
    # Resolve the children in the directory
    resolved_children: dict[str, Any] = {
        c.name: _resolve_child(
            c,
            missing_deserializer_policy=missing_deserializer_policy,
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
    # Identify and deserialize file
    if child.is_file():
        return _identify_and_deserialize_file(child, **kwargs)
    # Raise specific error on symlink
    if child.is_symlink():
        raise PilusDeserializeError(f"We don't support symlinks: {child}")
    # Raise general error for all other child types
    raise PilusDeserializeError(f"Unknown child: {child}")


def _identify_and_deserialize_file(
    file: Path,
    *,
    missing_deserializer_policy: MissingDeserializerPolicy,
    root: Path,
    manifest: Manifest,
) -> Any:
    """Identify file type using the manifest."""
    relative_path = file.relative_to(root)
    # Try to get the media type from the manifest.
    # Fall back on auto-detection of the media type.
    try:
        media_type = manifest.get_media_type(relative_path)
    except LookupError:
        media_type = detect_media_type(file)
    # Find preferred type
    try:
        file_spec = MediumSpec(raw_type=PathLike, media_type=media_type)
        output_type = FORGE._morphers.spec_to_type(file_spec)
        # Try to deserialize the file into a preferred type
        input_medium = Medium(raw=file, media_type=media_type)
        return FORGE.deserialize(input_medium, output_type)
    except (ValueError, PilusMissingMorpherError):
        medium: Medium
        if missing_deserializer_policy is MissingDeserializerPolicy.STORE_DATA:
            medium = Medium(raw=file.read_bytes(), media_type=media_type)
        elif missing_deserializer_policy is MissingDeserializerPolicy.STORE_METADATA:
            medium = Medium(raw=file, media_type=media_type)
        else:
            # We cover all `MissingDeserializerPolicy` values
            assert False
        return medium
