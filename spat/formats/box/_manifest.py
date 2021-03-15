from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema
from immutables import Map

from ._errors import BoxError

_MANIFEST_SCHEMA = {
    "type": "object",
    "properties": {
        "extensionToMediaType": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        }
    },
    "required": ["extensionToMediaType"],
}


@dataclass(frozen=True)
class Manifest:
    ext_to_media_type: Map[str, str]

    @classmethod
    def from_path(cls, path: Path) -> Manifest:
        try:
            with path.open("r") as f:
                data = f.read()
        except OSError as exc:
            raise BoxError(f"Could not open manifest file: {str(exc)}") from exc
        return cls.from_str(data)

    @classmethod
    def from_str(cls, data: str) -> Manifest:
        try:
            manifest_dict = json.loads(data)
        except json.JSONDecodeError as exc:
            raise BoxError(f"Could not parse manifest file: {str(exc)}") from exc
        try:
            jsonschema.validate(manifest_dict, _MANIFEST_SCHEMA)
        except jsonschema.ValidationError as exc:
            raise BoxError(f"Invalid manifest file: {str(exc)}") from exc
        ext_to_media_type: Map[str, str] = Map(**manifest_dict["extensionToMediaType"])
        return Manifest(ext_to_media_type)
