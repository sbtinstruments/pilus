from __future__ import annotations

from typing import ClassVar


class OdatChunk:
    """Currently not used."""

    type_: ClassVar[bytes] = b"oDAT"


class NoisChunk:
    """Currently not used."""

    type_: ClassVar[bytes] = b"nOIS"


class ExtrChunk:
    """Currently not used."""

    type_: ClassVar[bytes] = b"eXTR"


class PcexChunk:
    """Currently not used."""

    type_: ClassVar[bytes] = b"pCEX"


class BlinChunk:
    """Currently not used."""

    type_: ClassVar[bytes] = b"bLIN"


class RtraChunk:
    """Currently not used."""

    type_: ClassVar[bytes] = b"rTRA"


class MinfChunk:
    """Currently not used."""

    type_: ClassVar[bytes] = b"mINF"
