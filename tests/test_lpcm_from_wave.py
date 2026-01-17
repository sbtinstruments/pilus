from pathlib import Path

from pilus.basic import Lpcm

from ._assets import PUBLIC_ASSETS_DIR

WAVE_FILE = PUBLIC_ASSETS_DIR / Path("uncategorized/beat.wav")


def test_iqs_from_io() -> None:
    lpcm = Lpcm.from_file(WAVE_FILE)
    assert lpcm is not None
