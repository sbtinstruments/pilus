from pathlib import Path

from typing import Type, TypeVar, Union

import json
from pathlib import Path
from typing import Type, TypeVar, Union

import pydantic
from humps import decamelize

from .._errors import SpatJsonDecodeError, SpatValidationError, SpatOSError, SpatError


T = TypeVar("T")


def from_file(type_: Type[T], path: Path) -> T:
    try:
        with path.open("r") as f:
            data = f.read()
    except OSError as exc:
        raise SpatOSError(f"Could not open/read file: {str(exc)}") from exc
    if path.suffix == ".json":
        return from_json_data(type_, data)
    raise SpatError("Unknown file extension: {path.suffix}")


def from_json_data(type_: Type[T], data: Union[str, bytes]) -> T:
    try:
        obj_camel = json.loads(data)
    except json.JSONDecodeError as exc:
        raise SpatJsonDecodeError(f"Could not parse file: {str(exc)}") from exc
    obj_snake = decamelize(obj_camel)
    try:
        return pydantic.parse_obj_as(type_, obj_snake)
    except pydantic.ValidationError as exc:
        raise SpatValidationError(f"Invalid file: {str(exc)}") from exc
