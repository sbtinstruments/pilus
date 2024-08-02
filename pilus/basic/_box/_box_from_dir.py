import logging
from os import PathLike
from pathlib import Path
from typing import Annotated, Any, Literal

# from zipfile import ZipFile
from ..._magic import Medium, MediumSpec, detect_media_type
from ...errors import PilusDeserializeError
from ...forge import FORGE
from ._box import Box
from ._manifest import Manifest

_LOGGER = logging.getLogger(__name__)
_MANIFEST_PATH = Path("manifest.json")


StoreMode = Literal[
    "store-reference-to-data", "store-raw-data", "store-deserialized-data"
]


# TODO: Add a ZIP-based loader
# def from_file(file: Path) -> Box:
#     with ZipFile(file) as zf:
#         pass


@FORGE.register_deserializer
def box_from_dir(
    directory: Annotated[Path, "application/vnd.sbt.box"],
    *,
    mode: StoreMode | None = None,
    root: Path | None = None,
    manifest: Manifest | None = None,
) -> Box:
    """Return box based on the directory.

    Automatically deserializes the files in the directory based on the
    deserializers in the global registry.
    """
    # Default arguments
    if mode is None:
        mode = "store-reference-to-data"
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
            mode=mode,
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
        return box_from_dir(child, **kwargs)
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
    mode: StoreMode,
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

    # Store the raw (binary) data directly
    if mode == "store-raw-data":
        return Medium(raw=file.read_bytes(), media_type=media_type)

    # Store a reference (resolved file path) to the data.
    #
    # It's important that it's a resolved file path (and not, e.g., a relative file
    # path) since we don't have the `root` path of the box directory in the later
    # stages (e.g., when we want to actually load the file).
    input_medium = Medium(raw=file.resolve(), media_type=media_type)
    if mode == "store-reference-to-data":
        return input_medium

    # Attempt to deserialize the data using the first applicable
    # python type.
    assert mode == "store-deserialized-data"
    file_spec = MediumSpec(raw_type=PathLike, media_type=media_type)
    output_type = FORGE._morphers.spec_to_type(file_spec)
    return FORGE.deserialize(input_medium, output_type)
