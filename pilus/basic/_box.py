from typing import Any, TYPE_CHECKING

from immutables import Map

if TYPE_CHECKING:
    Box = Map[str, Any]
else:
    Box = Map
