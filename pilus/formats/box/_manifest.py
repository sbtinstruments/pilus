from __future__ import annotations

from pathlib import Path

from pydantic import Field

from ...model import Model, add_media_type


@add_media_type("application/vnd.sbt.box.manifest+json")
class Manifest(Model):
    """Manifest for the box format."""

    # TODO: Replace `dict` with `immutables.Map` when pydantic supports custom
    # data types.
    extension_to_media_type: dict[str, str] = Field(default_factory=dict)
    path_to_media_type: dict[Path, str] = Field(default_factory=dict)
