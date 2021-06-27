# We only import light-weight stuff at the module level
from ._errors import SpatError, SpatJsonDecodeError, SpatOSError, SpatValidationError
from ._parser_map import (
    IdentifiedData,
    IdentifiedIo,
    IdentifiedPath,
    IdentifiedResource,
    parse,
    register_parsers,
)
