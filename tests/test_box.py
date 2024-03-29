import json
from pathlib import Path

from immutables import Map
from pyfakefs.fake_filesystem import FakeFilesystem

from pilus._magic import Medium
from pilus.formats import box


def test_zip_as_box(fs: FakeFilesystem) -> None:
    fs.create_dir("project.box")
    fs.create_file(
        "project.box/manifest.json",
        contents="""
            {
                "extensionToMediaType": {
                    ".json": "application/json"
                }
            }
        """,
    )
    fs.create_file("project.box/data/my_numbers.json", contents="[1, 2, 3, 4]")
    project = box.from_dir(
        Path("project.box"),
        missing_deserializer_policy=box.MissingDeserializerPolicy.STORE_DATA,
    )
    data = project["data"]
    assert isinstance(data, Map)
    my_numbers = data["my_numbers.json"]
    assert isinstance(my_numbers, Medium)
    assert isinstance(my_numbers.raw, bytes)
    assert json.loads(my_numbers.raw) == [1, 2, 3, 4]
