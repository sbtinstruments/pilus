from datetime import timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from pilus.sbt import IqsAggregate
from pilus.sbt._format import iqs

from ._assets import PUBLIC_ASSETS_DIR

TEST_DATA = [
    (
        PUBLIC_ASSETS_DIR
        / Path("uncategorized/after2-measure-20191217-115350-0QX.iqs"),
        timedelta(microseconds=43),
    ),
    (
        PUBLIC_ASSETS_DIR / Path("uncategorized/NormalQC#3-bb2148006-D20.iqs"),
        timedelta(microseconds=0),
    ),
]

DURATION_THRESHOLD = timedelta(microseconds=0)


@pytest.mark.parametrize(("iqs_file", "duration_threshold"), TEST_DATA)
def test_iqs_from_io(iqs_file: Path, duration_threshold: timedelta) -> None:
    with iqs_file.open("rb") as io:
        data = iqs.from_io(io)
    assert data is not None
    duration = timedelta(microseconds=data.duration_ns * 1e-3)

    with NamedTemporaryFile() as temp_file:
        export_file = Path(temp_file.name)
        with export_file.open("wb") as io:
            iqs.to_io(data, io)
        with export_file.open("rb") as io:
            data_imported = iqs.from_io(io)

    assert data_imported is not None
    imported_duration = timedelta(microseconds=data_imported.duration_ns * 1e-3)

    delta = abs(duration - imported_duration)
    assert delta <= duration_threshold

    with NamedTemporaryFile() as temp_file:
        export_v1_file = Path(temp_file.name)
        with export_v1_file.open("wb") as io:
            iqs.to_io(data, io, version=iqs.IqsVersion.V1_0_0, site_to_keep="site1")
        with export_v1_file.open("rb") as io:
            data_v1_imported = iqs.from_io(io)

    assert data_v1_imported is not None
    imported_v1_duration = timedelta(microseconds=data_v1_imported.duration_ns * 1e-3)

    delta = abs(imported_duration - imported_v1_duration)
    assert delta <= duration_threshold

    # Try the methods on `IqsAggregate`
    iqs_aggregate = IqsAggregate.from_file(iqs_file)
    assert iqs_aggregate is not None
