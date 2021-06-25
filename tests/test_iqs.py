from datetime import datetime, timedelta
from pathlib import Path

from immutables import Map
from pytest import raises

from spat.formats import iqs

# FPA 2020-01-19: I don't want to include a large IQS file into the repo.
# We need to figure out how to do this properly. For now, just point the
# following path to an IQS file before you run the tests.
iqs_path: Path = Path("after2-measure-20191217-115350-0QX.iqs")


def test_load():
    snip = iqs.load(iqs_path)
    print(snip)
