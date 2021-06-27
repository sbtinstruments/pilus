from __future__ import annotations

from pathlib import Path

from pydantic import Field

from ...model import Model
from .._parser_map import register_parsers


class Manifest(Model):
    """Manifest for the box format."""

    json_media_type = "application/vnd.sbt.box.manifest+json"

    # TODO: Replace `dict` with `immutables.Map` when pydantic supports custom
    # data types.
    extension_to_media_type: dict[str, str] = Field(default_factory=dict)
    path_to_media_type: dict[Path, str] = Field(default_factory=dict)


register_parsers(Manifest.json_media_type, from_data=Manifest.from_json_data)
