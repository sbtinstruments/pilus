from pathlib import Path

import pytest

from pilus.basic import table_to_csv


@pytest.mark.usefixtures("fs")
def test_csv() -> None:
    table: list[list[str]] = [
        ["Eggs", "Spam"],
        ["2", "0"],
        ["1", "0"],
        ["0", "3"],
        ["0", "9"],
    ]
    data_file = Path("data_file.csv")
    table_to_csv(table, data_file)
    raw_text = data_file.read_text("utf8")
    assert isinstance(raw_text, str)
    assert raw_text == "Eggs,Spam\n2,0\n1,0\n0,3\n0,9\n"
