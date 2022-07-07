from __future__ import annotations

from pathlib import Path

from pydantic import Extra, Field

from ...forge import FORGE
from ...model import FrozenModel


@FORGE.register_model("application/vnd.sbt.box.manifest+json")
class Manifest(FrozenModel):
    """Manifest for the box format."""

    # TODO: Replace `dict` with `immutables.Map` when pydantic supports custom
    # data types.
    extension_to_media_type: dict[str, str] = Field(default_factory=dict)
    path_to_media_type: dict[Path, str] = Field(default_factory=dict)

    def get_media_type(self, file: Path) -> str:
        # First, try the path

        try:
            return self.path_to_media_type[file]
        except KeyError:
            pass
        # Second, try the extension
        ext = "".join(file.suffixes)
        try:
            return self.extension_to_media_type[ext]
        except KeyError as exc:
            raise LookupError(f'Manifest does not mention file "{file}"') from exc

    class Config:
        extra = Extra.forbid
