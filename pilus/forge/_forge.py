from collections.abc import Iterable
from contextlib import AbstractContextManager, ExitStack
from functools import partial, wraps
from itertools import chain
from os import PathLike
from pathlib import Path
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
from ._combiner import Combiner
from ._combiner_map import CombinerMap
from ._morph import (
    DeserializeFunc,
    Morpher,
    SerializeFunc,
    Shape,
    ShapeSpec,
    TransformFunc,
)
from ._morph_graph import MorphGraph
from ._run_once import run_once

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")
M = TypeVar("M", bound=BaseModel)

RegistrationFunc = Callable[["Forge"], None]


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
        self._combiners = CombinerMap()
        self._on_demand_registration_funcs: dict[str, Callable[[], None]] = {}

    def call_on_demand(
        self,
        *,
        type_repr_any_of: Iterable[str] = (),
        media_type_any_of: Iterable[str] = (),
    ) -> Callable[[RegistrationFunc], Callable[[], None]]:
        """Call the given function the first time that we encounter the given type.

        The returned function always work on this specific `Forge` instance and is
        idempotent.

        The on-demand behaviour is useful for types that come from "heavy" third-party
        libraries (e.g., numpy, scipy, pandas, polars, etc.). In essence, it allows you
        to defer the `import` of said libraries until the time of use. The benefits are
        three-fold:

         1. We don't impose heavy imports (e.g., numpy) on users that don't use it.
         2. It allows `Forge` itself to stay decoupled from specific types (e.g.,
            `numpy.ndarray`) and hence dependency-free.
         3. Our users can add as many types that they want to `Forge` (in an ad-hoc,
            plugin-like fashion) without having to worry about the import/dependency
            "costs" for other users.

        On the flip side, we rely on a string-based representation of the type. E.g.,

            repr(polars.Dataframe) == "<class 'polars.dataframe.frame.DataFrame'>"

        Note how the representation contains some internal structure as well (e.g.,
        the path to the specific submodule). If the representation changes, the
        on-demand behaviour fails to trigger.
        """

        def _decorator(func: RegistrationFunc) -> Callable[[], None]:
            idempotent_func = run_once(partial(func, self))

            # TODO: Find more efficient way than to simply add each and every one
            # to do a hash map. It's great for lookups (average case O(1)) though.
            for shape_repr in chain(type_repr_any_of, media_type_any_of):
                self._on_demand_registration_funcs[shape_repr] = idempotent_func

            return idempotent_func

        return _decorator

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

    def register_transformer(self, func: TransformFunc) -> TransformFunc:
        """Register the decorated transformer."""
        type_hints = get_type_hints(func, include_extras=False)
        # We expect that a transformer has a single argument
        first_arg_type = next(iter(type_hints.values()))
        return_type = type_hints["return"]
        morpher = Morpher(input=first_arg_type, output=return_type, func=func)
        self.add_morpher(morpher)
        # We don't change the function itself, we simply register it.
        return func

    def add_morpher(self, morpher: Morpher) -> None:
        self._morphers.add_morpher(morpher)

    def deserialize(self, input_medium: Medium, output_type: Type[T]) -> T:
        """Deserialize the input medium into the output type.

        This is just a convenience method that delegates the real work to `reshape`.
        """
        return self.reshape(input_medium, output_type)

    def transform(self, input_data: Any, output_type: Type[T]) -> T:
        """Transform the input data into the output type.

        This is just a convenience method that delegates the real work to `reshape`.
        """
        return self.reshape(input_data, output_type)

    def reshape(self, input_shape: Shape, output_type: type[T]) -> T:
        """Deserialize or transform the input shape into the output type.

        This is just a convenience method that delegates the real work to
        `get_reshape_func`.
        """
        func = self.get_reshape_func(input_shape, output_type)
        return func(input_shape)

    def get_reshape_func(
        self, input_shape: Shape, output_type: type[T]
    ) -> Callable[[Shape], T]:
        """Return function that deserializes/transforms the input shape.

        This method dynamically chains together a reshape function based on the
        available morphs in this forge.

        Raises `PilusMissingMorpherError` if it's impossible to construct the
        reshape function.
        """
        # Resolve input shape spec
        input_shape_spec: ShapeSpec
        if isinstance(input_shape, Medium):
            input_shape_spec = input_shape.spec
        else:
            input_shape_spec = type(input_shape)

        # On-demand registration of morphers for the arguments
        self._register_on_demand(input_shape)
        self._register_on_demand(output_type)

        # Find a sequence of morphs that takes us from the input medium
        # to the output type.
        morphs = tuple(self._morphers.get_morphs(input_shape_spec, output_type))

        def _reshape_func(shape_: Shape) -> T:
            result = shape_.raw if isinstance(shape_, Medium) else shape_
            with ExitStack() as stack:
                # Apply each morph in turn.
                for morph in morphs:
                    # Most morphs are simple, unary functions. Single input
                    # and single output.
                    assert isinstance(morph, (DeserializeFunc, TransformFunc))
                    result = morph(result)
                    # Some morphs, however, return context managers. E.g., to keep
                    # track of open file handles as done in `_file_to_io`. For these
                    # morphs, we use the `stack` to make sure that we close all open
                    # file handles afterwards.
                    result = _maybe_enter(stack, result)
            # TODO: Assert isinstance(result, output_type) instead here? Or is there
            # a problem with generics?
            return cast(T, result)

        return _reshape_func

    def convert(self, input_medium: Medium, output_medium: Medium) -> None:
        # On-demand registration of morphers for the arguments
        self._register_on_demand(input_medium)
        self._register_on_demand(output_medium)

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
                result = _maybe_enter(stack, result)

            last_morph = morphs[-1]
            assert isinstance(last_morph, SerializeFunc)
            last_morph(result, output_medium.raw)

    def serialize(self, input_data: Any, output_medium: Medium) -> None:
        # On-demand registration of morphers for the arguments
        self._register_on_demand(input_data)
        self._register_on_demand(output_medium)

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
                result = _maybe_enter(stack, result)
            last_morph = morphs[-1]
            assert isinstance(last_morph, SerializeFunc)
            last_morph(result, output_medium.raw)

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
                func=cls.model_validate_json,
            )
            self.add_morpher(morpher)
            return cls

        return _decorator

    def register_combiner(self, func: Callable[P, R]) -> Callable[P, R]:
        """Register the combiner."""
        combiner = Combiner(func)
        self._combiners.add_combiner(combiner)
        # We don't change the function itself, we simply register it.
        return func

    def _register_on_demand(self, shape: Shape) -> None:
        """Register additional morphers based on the given shape.

        This way, you don't have to `import` all dependencies up front. In turn,
        it allows `Forge` itself to stay light on dependencies. Want more functionality?
        simply add it on top via `register_on_demand` (plug-in style).
        """
        if isinstance(shape, Medium | MediumSpec):
            shape_repr = shape.media_type
        elif isinstance(shape, type):
            shape_repr = repr(shape)
        else:
            shape_repr = repr(type(shape))

        try:
            # We use `pop` so that we avoid multiple calls to the registration
            # function. It is merely a performance improvement (avoiding an
            # unncessary function call) for subsequent calls.
            #
            # Do note, however, that the same function may be called for
            # different shape_repr. Therefore `pop` alone is not enough. This
            # is why we wrap the register_func in `run_once` inside
            # `register_on_demand`.
            register_func = self._on_demand_registration_funcs.pop(shape_repr)
        except KeyError:
            pass
        else:
            register_func()


def _maybe_enter(stack: ExitStack, obj: Any) -> Any:
    # Special case for `pathlib.Path`: While technically a context manager (until
    # python 3.13), the enter/exit logic is a no-op. It also emits a deprecation
    # warning to enter/exit. Therefore, we do not add these objects to the stack.
    #
    # See: https://github.com/python/cpython/pull/30971
    if isinstance(obj, Path):
        return obj

    # Otherwise, add all (sync) context managers to the stack.
    if isinstance(obj, AbstractContextManager):
        return stack.enter_context(obj)

    # If we get this far, the object was not a context manager. We just return
    # the object as is.
    return obj
