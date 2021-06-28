from pathlib import Path


def split_at_suffixes(file_name: str) -> tuple[str, tuple[str, ...]]:
    """Split into (rest, suffixes).

    Examples:
        split_at_suffixes("source.tar.gz")  == ("source", (".tar", ".gz"))
        split_at_suffixes("source.tar.gz.") == ('source.tar.gz.', ())
        split_at_suffixes(".tar.gz")        == (".tar", (".gz",))
        split_at_suffixes("...source")      == ('...source', ())
    """
    path = Path(file_name)  # "source.tar.gz"
    suffixes = tuple(path.suffixes)  # (".tar", ".gz")
    suffixes_length = sum(len(s) for s in suffixes)  # 7 = 4 + 3
    rest = file_name[: len(file_name) - suffixes_length]  # "source"
    return (rest, suffixes)  # ("source", (".tar", ".gz"))
