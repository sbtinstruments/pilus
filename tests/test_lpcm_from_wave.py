from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

from pilus.basic import Lpcm

from ._assets import ASSETS_DIR

WAVE_FILE = ASSETS_DIR / Path("beat.wav")


def test_iqs_from_io(fs: FakeFilesystem) -> None:
    data_file = Path("beat.wav")
    fs.add_real_file(WAVE_FILE, target_path=data_file)
    lpcm = Lpcm.from_file(data_file)
    assert lpcm is not None
