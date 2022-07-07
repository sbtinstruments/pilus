from pathlib import Path
from typing import Optional

from typer import Option

from ...._magic import Medium
from ....forge import FORGE


def convert(
    input: Path,  # pylint: disable=redefined-builtin
    output: Path,
    *,
    input_media_type: Optional[str] = Option(None),
    output_media_type: Optional[str] = Option(None),
) -> None:
    """Convert input file to the given media type."""
    FORGE.convert(
        Medium.from_raw(input, media_type=input_media_type),
        Medium.from_raw(output, media_type=output_media_type),
    )
