from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from immutables import Map
from pytest import raises

from spat.formats import seed
from spat.types import Extremum, ExtremumType, Seed


def test_seed(fs) -> None:
    fs.create_dir("project")
    fs.create_file(
        "project/manifest.json",
        contents="""
            {
                "extensionToMediaType": {
                    ".extrema.json": "application/vnd.sbt.extrema+json"
                }
            }
        """,
    )
    fs.create_file(
        "project/data/part0--production.extrema.json",
        contents="""[
            {
                "timePoint": 123.000001,
                "value": 42.1,
                "type_": "Minimum"
            }
        ]""",
    )

    project = seed.from_dir(Path("project"))

    ms = timedelta(microseconds=1)
    x = datetime.fromtimestamp(123, timezone.utc) + ms

    extrema = project[Path("data/part0--production.extrema.json")]
    assert extrema == (Extremum(time_point=x, value=42.1, type_=ExtremumType.MINIMUM),)

    print(f"===== schema: {Extremum.schema()}")

    x = extrema[0].json()
    print(f"===== x: {x}")

    print(project)
