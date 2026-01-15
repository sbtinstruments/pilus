from ._idat import IdatChunk
from ._ihdr import IhdrChunk
from ._sdat import SdatChunk
from ._shdr import ShdrChunk

HeaderChunk = IhdrChunk | ShdrChunk
DataChunk = IdatChunk | SdatChunk
