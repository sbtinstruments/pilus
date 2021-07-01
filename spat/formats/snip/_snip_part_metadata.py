from __future__ import annotations

from typing import Any

from immutables import Map
from pydantic import BaseModel
from pydantic.fields import Field

from ...utility import find_duplicates, split_at_suffixes
from ._snip_attribute_declaration_map import SnipAttributeDeclarationMap
from ._snip_attributes import SnipAttribute

SnipAttributeMap = Map[str, SnipAttribute]


class SnipPartMetadata(BaseModel):
    """Metadata (name, attributes) for a snip part (deserialized file)."""

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

        Note that we discard the suffix(es) (e.g., ".wav").
        """
        # Example:
        #   "diff--site0--hf--im.wav-meta.json"
        # splits into
        #   ("diff--site0--hf--im", ".wav-meta.json")
        rest, _ = split_at_suffixes(file_name)
        # Get name and attribytes
        name, raw_attributes = _extract_raw_attribute(rest)
        # Parse raw attributes
        attributes: SnipAttributeMap = Map(
            attribute_declarations.parse_raw_attributes(raw_attributes)
        )
        return cls(name=name, attributes=attributes)

    class Config:  # pylint: disable=too-few-public-methods
        frozen = True
        # For `immutables.Map`
        # TODO: Add validator instead when pydantic supports custom data types.
        arbitrary_types_allowed = True


def create_attribute_map(
    attribute_declarations: SnipAttributeDeclarationMap, **kwargs: Any
) -> SnipAttributeMap:
    """Parse the kwargs into an attribute map."""
    return Map(attribute_declarations.parse_kwargs(**kwargs))


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
