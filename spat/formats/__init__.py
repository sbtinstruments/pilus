# We only import light-weight stuff at the module level
from ._errors import SpatError, SpatJsonDecodeError, SpatOSError, SpatValidationError
from ._parse import IdentifiedResource, Resource, parse, register_parsers
