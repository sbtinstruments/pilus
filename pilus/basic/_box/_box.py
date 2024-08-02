from typing import TYPE_CHECKING, Any

from immutables import Map

if TYPE_CHECKING:
    Box = Map[str, Any]
else:
    Box = Map
