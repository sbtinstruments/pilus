import csv
from pathlib import Path
from typing import Annotated, TypeVar

from ...basic import SimpleTable
from ...errors import PilusSerializeError
from ...forge import FORGE

T = TypeVar("T")


@FORGE.register_serializer
def table_to_file(table: SimpleTable, file: Annotated[Path, "text/csv"]) -> None:
    """Serialize table into the given file."""
    with file.open("wt", newline="") as text_io:
        try:
            writer = csv.writer(text_io, dialect=csv.excel)
            writer.writerows(table)
        except csv.Error as exc:
            raise PilusSerializeError(exc) from exc
