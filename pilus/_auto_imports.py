from pathlib import Path
from typing import Annotated, Any, BinaryIO

from .basic import BdrAggregate, Box, IqsAggregate, Lpcm, SimpleTable
from .forge import FORGE

# We want to avoid unnecessary imports (to save compute time and memory).
#
# Therefore, we register "dummy" (de)serializer functions here. As soon as
# these functions first run, they import the actual implementation and
# registers that.
#
# It works because the import will also call `register_deserializer`,
# which overrides the dummy function. In turn, subsequent `FORGE`
# requests (e.g., `FORGE.deserialize`) goes to the actual implementation.


@FORGE.register_deserializer
def bdr_from_io(io: Annotated[BinaryIO, "application/vnd.sbt.bdr"]) -> BdrAggregate:
    from .formats.bdr import from_io as _from_io

    return _from_io(io)


@FORGE.register_deserializer
def iqs_from_io(io: Annotated[BinaryIO, "application/vnd.sbt.iqs"]) -> IqsAggregate:
    from .formats.iqs import from_io as _from_io

    return _from_io(io)


@FORGE.register_deserializer
def wave_from_io(io: Annotated[BinaryIO, "audio/vnd.wave"]) -> Lpcm:
    from .formats.wave import from_io as _from_io

    return _from_io(io)


@FORGE.register_deserializer
def box_from_dir(
    directory: Annotated[Path, "application/vnd.sbt.box"], **kwargs: Any
) -> Box:
    from .formats.box import from_dir as _from_dir

    return _from_dir(directory, **kwargs)


@FORGE.register_serializer
def to_file(table: SimpleTable, file: Annotated[Path, "text/csv"]) -> None:
    from .formats.csv import table_to_file as _to_file

    return _to_file(table, file)
