from __future__ import annotations

from pathlib import Path

from pydantic.fields import Field
from pydantic.main import BaseModel

from ...utility import find_duplicates
from ._snip_attribute_declaration_map import SnipAttributeDeclarationMap
from ._snip_attributes import SnipAttribute

# TODO: Replace `dict` with `immutables.Map` when pydantic supports custom data types
SnipAttributeMap = dict[str, SnipAttribute]


class SnipPartMetadata(BaseModel):
    """Metadata (name, attributes) for a snip part (parsed file)."""

    name: str
    attributes: SnipAttributeMap = Field(default_factory=dict)

    @classmethod
    def from_file_name(
        cls, file_name: str, *, attribute_declarations: SnipAttributeDeclarationMap
    ) -> SnipPartMetadata:
        """Split a file name into the corresponding snip components.

        Take the following string for example:

            "diff--site0--hf--im.wav"

        We split this into:

            name: "diff"
            attributes: "site0", "hf", and "im"
        """
        # Example:
        #   "diff--site0--hf--im.wav-meta.json"
        # splits into
        #   ("diff--site0--hf--im", ".wav-meta.json")
        rest, _ = split_at_suffixes(file_name)
        # Get name and attribytes
        name, raw_attributes = _extract_raw_attribute(rest)
        # Parse raw attributes
        attributes = dict(attribute_declarations.parse_raw_attributes(raw_attributes))
        return cls(name=name, attributes=attributes)

    class Config:  # pylint: disable=too-few-public-methods
        frozen = True


def _extract_raw_attribute(rest: str) -> tuple[str, frozenset[str]]:
    parts = rest.split("--")
    assert parts, "There is always at least one element after a `split`"
    # The name is the first part
    name = parts.pop(0)
    # The remaining parts are the attributes
    duplicates = tuple(find_duplicates(parts))
    # We don't allow duplicates
    if duplicates:
        raise ValueError(f"We don't allow duplicate attributes: {duplicates}")
    raw_attributes = frozenset(parts)
    return (name, raw_attributes)


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
