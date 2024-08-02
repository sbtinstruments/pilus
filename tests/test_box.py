import json
from pathlib import Path

from immutables import Map
from pyfakefs.fake_filesystem import FakeFilesystem

from pilus._magic import Medium
from pilus.basic import box_from_dir


def test_store_raw_data(fs: FakeFilesystem) -> None:
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
    project = box_from_dir(
        Path("project.box"),
        mode="store-raw-data",
    )
    data = project["data"]
    assert isinstance(data, Map)
    my_numbers = data["my_numbers.json"]
    assert isinstance(my_numbers, Medium)
    assert isinstance(my_numbers.raw, bytes)
    assert json.loads(my_numbers.raw) == [1, 2, 3, 4]


def test_store_reference_to_data(fs: FakeFilesystem) -> None:
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
    project = box_from_dir(
        Path("project.box"),
        mode="store-reference-to-data",
    )
    data = project["data"]
    assert isinstance(data, Map)
    my_numbers = data["my_numbers.json"]
    assert isinstance(my_numbers, Medium)
    assert isinstance(my_numbers.raw, Path)
    assert my_numbers.media_type == "application/json"
    assert my_numbers.raw == Path("/project.box/data/my_numbers.json")
