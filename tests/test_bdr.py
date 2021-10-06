from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

from spat.formats.bdr import Bdr

bdr_path: Path = Path("test.bdr")


def test_iqs_from_io(fs: FakeFilesystem) -> None:
    fs.add_real_file("test.bdr", target_path="data.bdr")
    data_file = Path("data.bdr")
    with data_file.open("rb") as io:
        data = Bdr.from_io(io)
    assert data is not None
