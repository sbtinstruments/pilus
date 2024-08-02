from os import PathLike

from ..._magic import MediumSpec
from ...forge import FORGE, Morpher

FORGE.add_morpher(
    Morpher(
        input=MediumSpec(raw_type=PathLike, media_type="application/vnd.sbt.snip"),
        output=MediumSpec(raw_type=PathLike, media_type="application/vnd.sbt.box"),
        func=lambda x: x,
    )
)
