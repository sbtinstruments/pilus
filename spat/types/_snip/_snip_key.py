from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, TypeVar

from .._extremum import Extrema

AttributeSet = frozenset[str]

@dataclass(frozen=True)
class SnipKey:
    type_: type
    name: str
    attributes: AttributeSet = frozenset()

    @classmethod
    def from_file_name(cls, file_name: str) -> SnipKey:
        """Split a file name into the corresponding snip components.

        Take the following string for example:

            "diff--site0--hf--im.wav"

        We split this into:

            type_: `Wave`
            name: "diff"
            attributes: `frozenset` of "site0", "hf", and "im"
        """
        # Example:
        #   "diff--site0--hf--im.wav-meta.json"
        # splits into 
        #   ("diff--site0--hf--im", ".wav-meta.json")
        rest, suffixes = split_at_suffixes(file_name)
        # Get type from suffixes
        try:
            type_ = _SUFFIXES_TO_TYPE_MAP[suffixes]
        except KeyError as exc:
            raise ValueError(f'Unknown extension for file: "{file_name}"') from exc
        # Get name and attribytes
        name, attributes = extract_attributes(rest)
        return cls(type_, name, attributes)


_SUFFIXES_TO_TYPE_MAP = {
    (".extrema", ".json"): Extrema
}


def extract_attributes(rest: str) -> tuple[str, frozenset[str]]:
    parts = rest.split("--")
    assert parts, "There is always at least one element after a `split`"
    # The name is the first part
    name = parts.pop(0)
    # The remaining parts are the attributes
    duplicates = tuple(get_duplicates(parts))
    # We don't allow duplicates
    if duplicates:
        raise ValueError(f"We don't allow duplicate attributes: {duplicates}")
    attributes = frozenset(parts)
    return (name, attributes)


T = TypeVar("T")
def get_duplicates(data: Iterable[T]) -> Iterable[T]:
    """Return the duplicates in the given data.

    Total worst-case run-time: O(n*log(n))
    """
    seen = set()
    for datum in data:  # O(n)
        if datum in seen:
            yield datum
        seen.add(datum)  # O(log(n))


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
    rest = file_name[:len(file_name)-suffixes_length]  # "source"
    return (rest, suffixes)  # ("source", (".tar", ".gz"))
