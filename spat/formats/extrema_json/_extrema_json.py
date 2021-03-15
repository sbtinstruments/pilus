from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple, Union

import pydantic
from humps import decamelize

from ...types import Extrema
from ._errors import ExtremaJsonError


def from_path(path: Path) -> Extrema:
    try:
        with path.open("r") as f:
            data = f.read()
    except OSError as exc:
        raise ExtremaJsonError(f"Could not open/read file: {str(exc)}") from exc
    return from_data(data)


def from_data(data: Union[str, bytes]) -> Extrema:
    try:
        obj_camel = json.loads(data)
    except json.JSONDecodeError as exc:
        raise ExtremaJsonError(f"Could not parse file: {str(exc)}") from exc
    obj_snake = decamelize(obj_camel)
    try:
        return pydantic.parse_obj_as(Extrema, obj_snake)
    except pydantic.ValidationError as exc:
        raise ExtremaJsonError(f"Invalid file: {str(exc)}") from exc
