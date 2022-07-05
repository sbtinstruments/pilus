from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

from pilus.basic import Wave
from pilus.formats import wave as wav_format
from pilus.snipdb import SnipDb

from .assets import ASSETS_DIR

IQS_FILE = ASSETS_DIR / Path("after2-measure-20191217-115350-0QX.iqs")


def test_iqs_from_io(fs: FakeFilesystem) -> None:
    fs.add_real_file(IQS_FILE, target_path="data.iqs")
    data_file = Path("data.iqs")
    with data_file.open("rb") as io:
        snip_db = SnipDb.from_iqs_io(io)

    wave = snip_db.get(Wave)
    assert wave is not None

    wave_file = Path("data.wav")
    with wave_file.open("wb") as io:
        wav_format.to_io(wave.value.lpcm, io)
