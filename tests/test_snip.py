from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pytest import raises

from spat.formats import snip
from spat.types import Extrema, Extremum, ExtremumType


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
                "site": {
                    "type": "enum",
                    "values": ["site0", "site1"]
                },
                "frequency": {
                    "type": "enum",
                    "values": ["hf", "lf"]
                },
                "part": {
                    "type": "enum",
                    "values": ["re", "im"]
                },
                "settings": {
                    "type": "enum",
                    "values": ["production", "tuned-for-bacillus"]
                },
                "id": {
                    "type": "int"
                },
                "user": {
                    "type": "str"
                }
            }
        """,
    )
    fs.create_file(
        "project.snip/data/part0--production--id=32--user=1000.extrema.json",
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
    extrema_part = project.get(
        Extrema, name="part0", settings="production", id=32, user="1000"
    )
    assert extrema_part is not None
    extrema = extrema_part.value

    extrema_attributes = extrema_part.metadata.attributes
    assert extrema_attributes["settings"].value == "production"
    assert extrema_attributes["id"].value == 32
    assert extrema_attributes["user"].value == "1000"

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
