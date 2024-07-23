from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, Field

from ._snip_row_metadata import SnipRowMetadata

T = TypeVar("T")


class SnipRow(BaseModel, Generic[T], frozen=True):
    """Represents a single file inside a directory."""

    content: Annotated[
        T,
        Field(
            description="Content of the corresponding file in any shape (in-memory data, file path, or binary IO)"
        ),
    ]
    metadata: Annotated[
        SnipRowMetadata,
        Field(
            description="Metadata about the file that we extracted while parsing the file path"
        ),
    ]
