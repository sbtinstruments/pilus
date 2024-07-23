from __future__ import annotations

from typing import Annotated, Any

from immutables import Map
from pydantic import BaseModel, ConfigDict
from pydantic.fields import Field

from ..utility import find_duplicates, split_at_suffixes
from ._snip_attribute_declaration_map import SnipAttrDeclMap
from ._snip_attributes import SnipAttr

SnipAttributeMap = Map[str, SnipAttr]


class SnipRowMetadata(BaseModel):
    """Metadata (name, attributes) for a snip row."""

    model_config = ConfigDict(
        frozen=True,
        # For `immutables.Map`
        # TODO: Add validator instead when pydantic supports custom data types.
        arbitrary_types_allowed=True,
    )

    name: str
    attributes: Annotated[SnipAttributeMap, Field(default_factory=Map)]
    suffixes: tuple[str, ...] = tuple()

    @classmethod
    def from_file_name(
        cls, file_name: str, *, attr_decls: SnipAttrDeclMap
    ) -> SnipRowMetadata:
        """Split a file name into the corresponding snip components.

        Take the following string for example:

            "diff--site0--hf--im.fragments.wav"

        We split this into:

            name: "diff"
            attributes: "site0", "hf", and "im"
            suffixes: (".fragments", ".wav")

        """
        # Example:
        #   "diff--site0--hf--im.wav-meta.json"
        # splits into
        #   ("diff--site0--hf--im", ".wav-meta.json")
        rest, suffixes = split_at_suffixes(file_name)
        # Get name and attribytes
        name, raw_attributes = _extract_raw_attribute(rest)
        # Parse raw attributes
        attributes: SnipAttributeMap = Map(
            attr_decls.parse_raw_attributes(raw_attributes)
        )
        return cls(name=name, attributes=attributes, suffixes=suffixes)

    def exclude_tracing(self) -> SnipRowMetadata:
        """Return subset of this metadata that excludes traceability fields.

        In practice, this excludes the `suffixes` field since we only keep
        that around for traceability (e.g., "what kind of file did this come from?").
        """
        return SnipRowMetadata(name=self.name, attributes=self.attributes)


def create_attribute_map(
    attr_decls: SnipAttrDeclMap, **kwargs: Any
) -> SnipAttributeMap:
    """Parse the kwargs into an attribute map."""
    return Map(attr_decls.parse_kwargs(**kwargs))


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
