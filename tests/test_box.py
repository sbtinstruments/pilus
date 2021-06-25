import json
from pathlib import Path

from immutables._map import Map

from spat.formats import IdentifiedData, box


def test_zip_as_box(fs) -> None:
    fs.create_dir("project")
    fs.create_file(
        "project/manifest.json",
        contents="""
            {
                "extensionToMediaType": {
                    ".json": "application/json"
                }
            }
        """,
    )
    fs.create_file("project/data/my_numbers.json", contents="[1, 2, 3, 4]")
    project = box.from_dir(Path("project"))
    data = project["data"]
    assert isinstance(data, Map)
    my_numbers = data["my_numbers.json"]
    assert isinstance(my_numbers, IdentifiedData)
    assert json.loads(my_numbers.data) == [1, 2, 3, 4]
