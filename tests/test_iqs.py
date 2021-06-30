from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

from spat.formats import iqs

# FPA 2020-01-19: I don't want to include a large IQS file into the repo.
# We need to figure out how to do this properly. For now, just point the
# following path to an IQS file before you run the tests.
iqs_path: Path = Path("after2-measure-20191217-115350-0QX.iqs")


def test_iqs_from_io(fs: FakeFilesystem) -> None:
    fs.add_real_file("after2-measure-20191217-115350-0QX.iqs", target_path="data.iqs")
    data_file = Path("data.iqs")
    with data_file.open("rb") as io:
        data = iqs.from_io(io)
    assert data is not None
    duration_s = data.idat.duration_ns * 1e-9
    print(f"{duration_s=:.1f}")

    export_file = Path("data_export.iqs")
    with export_file.open("wb") as io:
        iqs.to_io(data, io)

    with export_file.open("rb") as io:
        data_imported = iqs.from_io(io)
    assert data_imported is not None
    imported_duration_s = data_imported.idat.duration_ns * 1e-9
    print(f"{imported_duration_s=:.1f}")

    assert duration_s == imported_duration_s
