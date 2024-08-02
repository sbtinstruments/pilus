from datetime import datetime, timedelta, timezone
from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem
from tinydb import where

from pilus._magic import Medium
from pilus.basic import Lpcm, Wave, WaveMeta
from pilus.sbt import Extrema, Extremum, ExtremumType
from pilus.snipdb import SnipDb, SnipRow

from ._assets import ASSETS_DIR


def test_snip(fs: FakeFilesystem) -> None:
    fs.create_dir("project.snip")
    fs.create_file(
        "project.snip/manifest.json",
        contents="""
            {
                "extensionToMediaType": {
                    ".extrema.json": "application/vnd.sbt.extrema+json",
                    ".wav": "audio/vnd.wave",
                    ".wave-meta.json": "application/vnd.sbt.wave-meta+json"
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
                "type_": "maximum"
            },
            {
                "timePoint": 143,
                "value": -8.8,
                "type_": "minimum"
            }
        ]""",
    )
    fs.add_real_file(ASSETS_DIR / "beat.wav", target_path="project.snip/data/part0.wav")
    fs.create_file(
        "project.snip/data/part0.wave-meta.json",
        contents="""
            {
                "startTime": 1231231231,
                "maxAmplitude": 123
            }
        """,
    )

    project = SnipDb.from_dir(Path("project.snip"))

    for row in project:
        assert isinstance(row, SnipRow)
        assert isinstance(row.content, Medium)

    medium = project.get_one(
        Medium, where("name") == "part0", settings="production", user="1000"
    )
    assert isinstance(medium, Medium)
    assert isinstance(medium.raw, Path)
    assert medium.media_type == "application/vnd.sbt.extrema+json"

    extrema_part = project.get_one(
        SnipRow[Extrema],
        where("name") == "part0",
        where("suffixes") == (".extrema", ".json"),
        settings="production",
        id=32,
        user="1000",
    )
    extrema = extrema_part.content

    extrema_attributes = extrema_part.metadata.attributes
    assert extrema_attributes["settings"].value == "production"
    assert extrema_attributes["id"].value == 32
    assert extrema_attributes["user"].value == "1000"
    extrema_suffixes = extrema_part.metadata.suffixes
    assert extrema_suffixes == (".extrema", ".json")

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

    print("=======")
    for row in project:
        print(f"{type(row.content)=} {row.metadata=}")

    # Snip automatically combines the `.wav` and `.wave-meta.json` into one when
    # we query for `Wave`.
    wave = project.get_one(Wave)
    assert isinstance(wave, Wave)
    assert wave.lpcm.byte_depth == 2

    # We can stil get individual (non-combined) parts if we want to
    wave_meta = project.get_one(WaveMeta)
    assert isinstance(wave_meta, WaveMeta)
    lpcm = project.get_one(Lpcm)
    assert isinstance(lpcm, Lpcm)
