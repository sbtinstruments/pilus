from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

from spat.basic import Wave
from spat.formats import wave as wav_format
from spat.snipdb import SnipDb

# FPA 2020-01-19: I don't want to include a large IQS file into the repo.
# We need to figure out how to do this properly. For now, just point the
# following path to an IQS file before you run the tests.
iqs_path: Path = Path("after2-measure-20191217-115350-0QX.iqs")


def test_iqs_from_io(fs: FakeFilesystem) -> None:
    fs.add_real_file("after2-measure-20191217-115350-0QX.iqs", target_path="data.iqs")
    data_file = Path("data.iqs")
    with data_file.open("rb") as io:
        snip_db = SnipDb.from_iqs_io(io)

    wave = snip_db.get(Wave)
    assert wave is not None
    # print(f"{wave=}")

    wave_file = Path("data.wav")
    with wave_file.open("wb") as io:
        wav_format.to_io(wave.value.lpcm, io)
