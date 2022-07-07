from typing import Any

from ..basic import Lpcm
from ..snipdb import SnipDb

# Mapping of media type to type.
# We use this mapping when we, e.g., deserialize files from the box/snip
# container format.
PREFERRED_TYPES: dict[str, Any] = {}
