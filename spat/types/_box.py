from typing import Any

# We explicitly import the `_map` file to get the proper typing (corresponding to the
# `_map.pyi` file).
from immutables._map import Map

BoxValue = Any
Box = Map[str, Any]
