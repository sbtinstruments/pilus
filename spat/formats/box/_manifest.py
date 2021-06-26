from pathlib import Path

from pydantic import Field

from ..model import Model


class Manifest(Model):
    """Manifest for the box format.

    Media type: "application/vnd.sbt.box.manifest+json"
    """

    # TODO: Replace `dict` with `immutables.Map` when pydantic supports custom
    # data types.
    extension_to_media_type: dict[str, str] = Field(default_factory=dict)
    path_to_media_type: dict[Path, str] = Field(default_factory=dict)
