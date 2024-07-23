from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

from pilus.basic import Wave
from pilus.formats import wave as wav_format
from pilus.snipdb import SnipDb

from ._assets import ASSETS_DIR

IQS_FILE = ASSETS_DIR / Path("after2-measure-20191217-115350-0QX.iqs")


def test_iqs_from_io(fs: FakeFilesystem) -> None:
    data_file = Path("data.iqs")
    fs.add_real_file(IQS_FILE, target_path=data_file)
    snip_db = SnipDb.from_file(data_file)

    wave = snip_db.get_first(Wave)
    assert isinstance(wave, Wave)

    wave = snip_db.get_one(Wave, site="site0", channel="hf", part="re")
    assert isinstance(wave, Wave)

    wave_file = Path("data.wav")
    with wave_file.open("wb") as io:
        wav_format.to_io(wave.lpcm, io)
