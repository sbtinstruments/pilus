from datetime import timedelta
from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

from spat.formats import iqs

from .assets import ASSETS_DIR

TEST_DATA = [
    (ASSETS_DIR / Path("after2-measure-20191217-115350-0QX.iqs"), timedelta(microseconds=43)),
    (ASSETS_DIR / Path("NormalQC#3-bb2148006-D20.iqs"), timedelta(microseconds=0)),
]

DURATION_THRESHOLD = timedelta(microseconds=0)


def test_iqs_from_io(fs: FakeFilesystem) -> None:
    for iqs_file, duration_threshold in TEST_DATA:
        fs.reset()
        fs.add_real_file(iqs_file, target_path="data.iqs")
        data_file = Path("data.iqs")
        with data_file.open("rb") as io:
            data = iqs.from_io(io)
        assert data is not None
        duration = timedelta(microseconds=data.duration_ns * 1e-3)

        export_file = Path("data_export.iqs")
        with export_file.open("wb") as io:
            iqs.to_io(data, io)

        with export_file.open("rb") as io:
            data_imported = iqs.from_io(io)
        assert data_imported is not None
        imported_duration = timedelta(microseconds=data_imported.duration_ns * 1e-3)

        delta = abs(duration - imported_duration)
        assert delta <= duration_threshold

        export_v1_file = Path("data_export_v1.iqs")
        with export_v1_file.open("wb") as io:
            iqs.to_io(data, io, version=iqs.IqsVersion.V1_0_0, site_to_keep="site1")

        with export_v1_file.open("rb") as io:
            data_v1_imported = iqs.from_io(io)
        assert data_v1_imported is not None
        imported_v1_duration = timedelta(microseconds=data_v1_imported.duration_ns * 1e-3)

        delta = abs(imported_duration - imported_v1_duration)
        assert delta <= duration_threshold
