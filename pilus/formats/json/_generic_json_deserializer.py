import json
from typing import Any, Type, TypeVar

from humps import decamelize
from pydantic import ValidationError, parse_obj_as

from ...errors import PilusJsonDecodeError, PilusValidationError

T = TypeVar("T")


def from_json_data(type_: Type[T], data: bytes) -> T:
    """Deserialize binary data into an instance of the given type.

    This is a generic method that works with built-in types and pydantic models.
    """
    try:
        obj_camel = json.loads(data)
    except json.JSONDecodeError as exc:
        raise PilusJsonDecodeError(exc.msg, exc.doc, exc.pos) from exc
    return from_json_obj(type_, obj_camel)


def from_json_obj(type_: Type[T], obj_camel: Any) -> T:
    """Deserialize object into an instance of the given type.

    This is a generic method that works with built-in types and pydantic models.
    """
    obj_snake = decamelize(obj_camel)
    try:
        return parse_obj_as(type_, obj_snake)
    except ValidationError as exc:
        raise PilusValidationError(exc.raw_errors, exc.model) from exc
