from contextlib import AbstractContextManager, ExitStack
from os import PathLike
from typing import (
    Any,
    BinaryIO,
    Callable,
    ParamSpec,
    Type,
    TypeVar,
    cast,
    get_args,
    get_type_hints,
)

from pydantic import BaseModel

from .._magic import Medium, MediumSpec, RawMediumType
from ._merger import Merger
from ._merger_map import MergerMap
from ._morph import DeserializeFunc, Morpher, SerializeFunc, TransformFunc
from ._morph_graph import MorphGraph

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")
M = TypeVar("M", bound=BaseModel)


class Forge:
    """One-stop toolbox to convert/deserialize/serialize/transform data.

    That was a mouthful. In more detail, this class can:

     * Convert: Change *medium* from *media type* A to *media type* B.
     * Deserialize: Load *medium* in *media type* A to *in-memory data* in
       *data type* B.
     * Serialize: Save *in-memory data* of *data type* A as *medium* in *media type* B.
     * Transform: Change *in-memory data* of *data type A* to *data type* B.
     * Combine: Merge *in-memory data* of two or more *data type*s in a single
       *data type*.
     * Split: **Not yet implemented**.

    Note that we are strict about the terminology here:

     * Medium: Reference to data. E.g., a file path, IO stream, pointer to memory, etc.
       The data is of a specific *media type*.
     * In-memory data: Data that resides in main memory (usually RAM) owned by the
       current process.
     * Data type: Python representation of in-memory data. E.g., `list[int]`,
       `pydantic.BaseModel`, `dict[str, pydantic.BaseModel]`, etc.
     * Media type: Defined by RFC6838
       See: https://www.iana.org/assignments/media-types/media-types.xhtml
     * Shape: Either *in-memory data* or *medium*.

    Internally, we use *morph* to refer to any of convert, deserialize, serialize,
    or transform. Note that *combine* is not part of this list.
    """

    def __init__(self) -> None:
        self._morphers = MorphGraph()
        self._mergers = MergerMap()

    def register_deserializer(self, func: Callable[P, R]) -> Callable[P, R]:
        """Register the decorated deserializer."""
        type_hints = get_type_hints(func, include_extras=True)
        first_arg_annotations = get_args(next(iter(type_hints.values())))
        first_arg_type = first_arg_annotations[0]
        media_type = first_arg_annotations[1]
        raw_type: RawMediumType
        if issubclass(first_arg_type, BinaryIO):
            raw_type = BinaryIO
        elif issubclass(first_arg_type, PathLike):
            raw_type = PathLike
        else:
            ValueError("Unsupported first argument type")
        input_spec = MediumSpec(raw_type=raw_type, media_type=media_type)
        output_spec = type_hints["return"]
        morpher = Morpher(input=input_spec, output=output_spec, func=func)
        self.add_morpher(morpher)
        # We don't change the function itself, we simply register it.
        return func

    def register_serializer(self, func: SerializeFunc) -> SerializeFunc:
        """Register the decorated serializer."""
        type_hints = iter(get_type_hints(func, include_extras=True).values())
        # We expect that a serialize has only two arguments
        arg_annotations: tuple[type, tuple[type, str]] = (
            next(type_hints),
            get_args(next(type_hints)),
        )
        input_type = arg_annotations[0]
        arg_raw_type = arg_annotations[1][0]
        output_media_type = arg_annotations[1][1]
        output_raw_type: RawMediumType
        if issubclass(arg_raw_type, BinaryIO):
            output_raw_type = BinaryIO
        elif issubclass(arg_raw_type, PathLike):
            output_raw_type = PathLike
        else:
            ValueError("Unsupported first argument type")
        output_spec = MediumSpec(raw_type=output_raw_type, media_type=output_media_type)
        morpher = Morpher(input=input_type, output=output_spec, func=func)
        self.add_morpher(morpher)
        # We don't change the function itself, we simply register it.
        return func

    def add_morpher(self, morpher: Morpher) -> None:
        self._morphers.add_morpher(morpher)

    def convert(self, input_medium: Medium, output_medium: Medium) -> None:
        # Find a sequence of morphs that takes us from the input medium
        # to the output type.
        morphs = tuple(self._morphers.get_morphs(input_medium.spec, output_medium.spec))
        with ExitStack() as stack:
            result: Any = input_medium.raw
            # Apply each morph in turn.
            assert len(morphs) >= 1
            for morph in morphs[:-1]:
                # Most morphs are simple, unary functions. Single input
                # and single output.
                assert isinstance(morph, TransformFunc)
                result = morph(result)
                # Some morphs, however, return context managers. E.g., to keep
                # track of open file handles. For these morphs, we use the
                # `stack` to make sure that we close all open file handles afterwards.
                if isinstance(result, AbstractContextManager):
                    result = stack.enter_context(result)
            last_morph = morphs[-1]
            assert isinstance(last_morph, SerializeFunc)
            last_morph(result, output_medium.raw)

    def deserialize(self, input_medium: Medium, output_type: Type[T]) -> T:
        # Find a sequence of morphs that takes us from the input medium
        # to the output type.
        morphs = self._morphers.get_morphs(input_medium.spec, output_type)
        with ExitStack() as stack:
            result: Any = input_medium.raw
            # Apply each morph in turn.
            for morph in morphs:
                # Most morphs are simple, unary functions. Single input
                # and single output.
                assert isinstance(morph, (DeserializeFunc, TransformFunc))
                result = morph(result)
                # Some morphs, however, return context managers. E.g., to keep
                # track of open file handles. For these morphs, we use the
                # `stack` to make sure that we close all open file handles afterwards.
                if isinstance(result, AbstractContextManager):
                    result = stack.enter_context(result)
        return cast(T, result)

    def serialize(self, input_data: Any, output_medium: Medium) -> None:
        # Find a sequence of morphs that takes us from the input medium
        # to the output type.
        morphs = tuple(self._morphers.get_morphs(type(input_data), output_medium.spec))
        with ExitStack() as stack:
            result: Any = input_data
            # Apply each morph in turn.
            assert len(morphs) >= 1
            for morph in morphs[:-1]:
                # Most morphs are simple, unary functions. Single input
                # and single output.
                assert isinstance(morph, TransformFunc)
                result = morph(result)
                # Some morphs, however, return context managers. E.g., to keep
                # track of open file handles. For these morphs, we use the
                # `stack` to make sure that we close all open file handles afterwards.
                if isinstance(result, AbstractContextManager):
                    result = stack.enter_context(result)
            last_morph = morphs[-1]
            assert isinstance(last_morph, SerializeFunc)
            last_morph(result, output_medium.raw)

    def transform(self, input_data: Any, output_type: Type[T]) -> T:
        raise NotImplementedError()

    def register_model(self, media_type: str) -> Callable[[Type[M]], Type[M]]:
        """Associate the class with the given media type.

        This enables auto-generated serialization/deserialization methods on the class.
        """
        # Early out on unsupported media types
        if not media_type.endswith("+json"):
            raise ValueError('Only supports media types with the "+json" suffix')

        def _decorator(cls: Type[M]) -> Type[M]:
            morpher = Morpher(
                input=MediumSpec(raw_type=bytes, media_type=media_type),
                output=cls,
                func=cls.parse_raw,
            )
            self.add_morpher(morpher)
            return cls

        return _decorator

    def register_combiner(self, func: Callable[P, R]) -> Callable[P, R]:
        """Register the merger."""
        merger = Merger(func)
        self._mergers.add_merger(merger)
        # We don't change the function itself, we simply register it.
        return func
