import json
from typing import Type, TypeVar

from humps import decamelize
from pydantic import ValidationError, parse_obj_as

from .._errors import SpatJsonDecodeError, SpatValidationError

T = TypeVar("T")


def from_json_data(type_: Type[T], data: bytes) -> T:
    """Return instance of the given type from the JSON representation.

    This is a generic method that works with built-in types and pydantic models.
    """
    try:
        obj_camel = json.loads(data)
    except json.JSONDecodeError as exc:
        raise SpatJsonDecodeError(exc.msg, exc.doc, exc.pos) from exc
    obj_snake = decamelize(obj_camel)
    try:
        return parse_obj_as(type_, obj_snake)
    except ValidationError as exc:
        raise SpatValidationError(exc.raw_errors, exc.model) from exc
