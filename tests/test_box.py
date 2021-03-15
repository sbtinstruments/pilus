from datetime import datetime, timedelta
from pathlib import Path

import pytest
from immutables import Map
from pytest import raises

from spat.formats import box
from spat.types import Box


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

    my_numbers = project[Path("data/my_numbers.json")]
    print(f"my_numbers: {my_numbers}")

    print(project)
