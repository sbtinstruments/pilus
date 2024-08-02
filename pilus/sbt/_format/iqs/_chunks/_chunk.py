from typing import Union

from ._idat import IdatChunk
from ._ihdr import IhdrChunk
from ._sdat import SdatChunk
from ._shdr import ShdrChunk

HeaderChunk = Union[IhdrChunk, ShdrChunk]
DataChunk = Union[IdatChunk, SdatChunk]
