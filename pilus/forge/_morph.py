from dataclasses import dataclass
from typing import Any, Callable, Protocol, Union, runtime_checkable

from .._magic import MediumSpec, RawMedium

# A shape is either:
#  1. In-memory data (e.g., a list of integers or pydantic model)
#  2. A medium (e.g., a file path or binary data)
# Due to (1), the a shape can by of any type (I.e. `Any`). Therefore,
# there is no reason to specify (2) as well. In fact, we use
# `Union[Any, Medium]` we just run into covariance/contravariance problems
# later in.
Shape = Any  # Any | Medium
RawShape = Any  # Any | RawMedium
ShapeSpec = type | MediumSpec


@runtime_checkable
class ConvertFunc(Protocol):
    def __call__(self, __input_medium: RawMedium, __output_medium: RawMedium) -> None:
        ...


@runtime_checkable
class DeserializeFunc(Protocol):
    def __call__(self, __input_medium: RawMedium) -> Any:
        ...


@runtime_checkable
class SerializeFunc(Protocol):
    # We use type `Any` for `__output_medium` (and not `RawMedium`) to avoid
    # covariance/contravariance issues.
    def __call__(self, __input_data: Any, __output_medium: Any) -> None:
        ...


# Note that `TransformFunc` is very lenient. Effectively, it makes
# `Deserializefunc` redundant. We keep the latter around for completeness.
# The `Any` return type also covers the need for transform functions that return
# context managers.
@runtime_checkable
class TransformFunc(Protocol):
    def __call__(self, __input_data: Any) -> Any:
        ...


MorphFunc = Union[ConvertFunc, DeserializeFunc, SerializeFunc, TransformFunc]


@dataclass(frozen=True)
class Morpher:
    """Holds a function that morphs input to output."""

    input: ShapeSpec
    output: ShapeSpec
    func: MorphFunc
