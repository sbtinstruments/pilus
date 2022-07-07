from datetime import datetime, timedelta, timezone
from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

from pilus.basic import Extrema, Extremum, ExtremumType, Wave, WaveMeta
from pilus.snipdb import SnipDb

from .assets import ASSETS_DIR


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

    print("=======")
    for part in project:
        print(f"{type(part.value)=} {part.metadata=}")

    wave_part = project.get(Wave)
    assert wave_part is not None
    wave = wave_part.value
    assert wave.lpcm.byte_depth == 2

    wave_meta_part = project.get(WaveMeta)
    # We merge `WaveMeta` into `Wave`, so the former isn't present in the output
    assert wave_meta_part is None
