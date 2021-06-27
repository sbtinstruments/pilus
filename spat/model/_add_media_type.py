from typing import Callable, Type, TypeVar

from ..formats import register_parsers
from ..formats.json import from_json_data
from ._model import Model

T = TypeVar("T", bound=Model)


def add_media_type(media_type: str) -> Callable[[Type[T]], Type[T]]:
    """Associate the class with the given media type.

    This enables auto-generated serialization/deserialization methods on the class.
    """
    # Early out on unsupported media types
    if not media_type.endswith("+json"):
        raise ValueError('Only supports media types with the "+json" suffix')

    def _decorator(cls: Type[T]) -> Type[T]:
        # Early out on conflict
        if any(mt.endswith("+json") for mt in cls.media_types):
            raise ValueError(
                f'Class "{cls.__name__}" is already associated with a '
                "JSON-suffixed media type"
            )

        class _Decorated(cls):
            # When we add the media type to the list, the
            # serialization/deserialization methods start to work.
            media_types = cls.media_types + (media_type,)

        # Forward name and doc
        _Decorated.__name__ = cls.__name__
        _Decorated.__doc__ = cls.__doc__
        # Create JSON data parser
        from_data = lambda data: from_json_data(_Decorated, data)
        # Register the parser for the media type
        register_parsers(media_type, from_data=from_data)

        return _Decorated

    return _decorator
