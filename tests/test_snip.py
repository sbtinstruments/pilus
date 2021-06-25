from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from immutables import Map
from pytest import raises

from spat.formats import snip
from spat.types import Extrema, Extremum, ExtremumType, Snip


def test_snip(fs) -> None:
    fs.create_dir("project.snip")
    fs.create_file(
        "project.snip/manifest.json",
        contents="""
            {
                "extensionToMediaType": {
                    ".extrema.json": "application/vnd.sbt.extrema+json"
                },
                "pathToMediaType": {
                    "attributes.json": "application/vnd.sbt.snip.attributes+json"
                }
            }
        """,
    )
    fs.create_file(
        "project.snip/attributes.json",
        contents="""
            {
                "types": {
                    "enums": {
                        "site": {
                            "values": ["site0", "site1"]
                        },
                        "frequency": {
                            "values": ["hf", "lf"]
                        },
                        "part": {
                            "values": ["re", "im"]
                        },
                        "settings": {
                            "values": ["production", "tuned-for-bacillus"]
                        }
                    }
                }
            }
        """,
    )
    fs.create_file(
        "project.snip/data/part0--production.extrema.json",
        contents="""[
            {
                "timePoint": 123.000001,
                "value": 42.1,
                "type_": "Maximum"
            },
            {
                "timePoint": 143,
                "value": -8.8,
                "type_": "Minimum"
            }
        ]""",
    )

    project = snip.from_dir(Path("project.snip"))
    extrema_part = project.get(Extrema, name="part0", attributes=("production",))
    assert extrema_part is not None
    extrema = extrema_part.value

    one_us = timedelta(microseconds=1)
    assert extrema == (
        Extremum(
            time_point=datetime.fromtimestamp(123, timezone.utc) + one_us,
            value=42.1,
            type_=ExtremumType.MAXIMUM,
        ),
        Extremum(
            time_point=datetime.fromtimestamp(143, timezone.utc),
            value=-8.8,
            type_=ExtremumType.MINIMUM,
        ),
    )
