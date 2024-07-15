from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

from pilus._magic import Medium
from pilus.basic import BdrAggregate
from pilus.forge import FORGE

from ._assets import ASSETS_DIR

BDR_FILE = ASSETS_DIR / Path("measure-bb2221028-A02.bdr")


def test_bdr_from_io(fs: FakeFilesystem) -> None:
    fs.add_real_file(BDR_FILE, target_path="data.bdr")
    data_file = Path("data.bdr")

    bdr_aggregate = BdrAggregate.from_file(data_file)
    assert bdr_aggregate is not None

    with data_file.open("rb") as io:
        bdr_aggregate = BdrAggregate.from_io(io)
    assert bdr_aggregate is not None

    # TODO: Replace with `to_file` from `ForgeIO` or similar
    csv_file = Path("data.csv")
    FORGE.serialize(bdr_aggregate, Medium.from_raw(csv_file))
    # print(f"{csv_file.read_text()[:10000]=}")
