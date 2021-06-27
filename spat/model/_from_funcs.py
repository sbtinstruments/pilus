import json
from pathlib import Path
from typing import BinaryIO, Type, TypeVar, Union

import pydantic
from humps import decamelize

from ..formats import SpatJsonDecodeError, SpatValidationError

T = TypeVar("T")


def from_json_data(type_: Type[T], data: Union[str, bytes]) -> T:
    try:
        obj_camel = json.loads(data)
    except json.JSONDecodeError as exc:
        raise SpatJsonDecodeError(exc.msg, exc.doc, exc.pos) from exc
    obj_snake = decamelize(obj_camel)
    try:
        return pydantic.parse_obj_as(type_, obj_snake)
    except pydantic.ValidationError as exc:
        raise SpatValidationError(exc.raw_errors, exc.model) from exc
