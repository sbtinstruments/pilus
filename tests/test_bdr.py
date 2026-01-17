from pathlib import Path
from tempfile import TemporaryDirectory

from pilus._magic import Medium
from pilus.forge import FORGE
from pilus.sbt import BdrAggregate

from ._assets import PUBLIC_ASSETS_DIR

_BDR_FILE = PUBLIC_ASSETS_DIR / "uncategorized/measure-bb2221028-A02.bdr"


def test_bdr_from_io() -> None:
    data_file = _BDR_FILE

    bdr_aggregate = BdrAggregate.from_file(data_file)
    assert bdr_aggregate is not None

    with data_file.open("rb") as io:
        bdr_aggregate = BdrAggregate.from_io(io)
    assert bdr_aggregate is not None

    with TemporaryDirectory() as temp_dir:
        csv_file = Path(temp_dir) / " data.csv"
        # TODO: Replace with `to_file` from `ForgeIO` or similar
        FORGE.serialize(bdr_aggregate, Medium.from_raw(csv_file))
