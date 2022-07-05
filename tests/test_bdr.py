from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

from spat.formats.bdr import Bdr

from .assets import ASSETS_DIR

BDR_FILE = ASSETS_DIR/ Path("measure-bb2221028-A02.bdr")


def test_iqs_from_io(fs: FakeFilesystem) -> None:
    fs.add_real_file(BDR_FILE, target_path="data.bdr")
    data_file = Path("data.bdr")
    with data_file.open("rb") as io:
        data = Bdr.from_io(io)
    assert data is not None
