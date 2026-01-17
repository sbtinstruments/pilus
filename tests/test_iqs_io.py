from pathlib import Path
from tempfile import TemporaryDirectory

import polars as pl
from pilus._magic import Medium
from pilus.basic import Wave, lpcm_to_io
from pilus.forge import FORGE
from pilus.snipdb import SnipDb

from ._assets import PUBLIC_ASSETS_DIR

_IQS_FILE = PUBLIC_ASSETS_DIR / "uncategorized/after2-measure-20191217-115350-0QX.iqs"


def test_iqs_to_snipdb() -> None:
    snip_db = SnipDb.from_file(_IQS_FILE)

    wave = snip_db.get_first(Wave)
    assert isinstance(wave, Wave)

    wave = snip_db.get_one(Wave, site="site0", channel="hf", part="re")
    assert isinstance(wave, Wave)

    with TemporaryDirectory() as temp_dir:
        wave_file = Path(temp_dir) / "data.wav"
        with wave_file.open("wb") as io:
            lpcm_to_io(wave.lpcm, io)


def test_iqs_to_polars() -> None:
    df = FORGE.deserialize(Medium.from_raw(_IQS_FILE), pl.DataFrame)

    # Check the overall dimensionality and metadata
    assert set(df.columns) == {
        "site0-hf-re",
        "site0-hf-im",
        "site0-lf-re",
        "site0-lf-im",
        "site1-hf-re",
        "site1-hf-im",
        "site1-lf-re",
        "site1-lf-im",
        "time",
    }
    assert len(df) == 2058150

    # Check some specific (yet arbitrary) data points
    assert df["site0-hf-re"].head(1).to_list() == [0.0008609048333187107]
    assert df["site0-hf-re"].tail(1).to_list() == [0.0008100454626730188]
    # Nanoseconds since the UNIX epoch
    assert df["time"].head(1).cast(int).to_list() == [1576580031051702000]
    assert df["time"].tail(1).cast(int).to_list() == [1576580120885789552]
