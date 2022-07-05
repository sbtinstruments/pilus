from __future__ import annotations

from dataclasses import dataclass

from typing import TYPE_CHECKING, BinaryIO, ClassVar, Optional


@dataclass(frozen=True)
class OdatChunk:
    """Currently not used."""

    type_: ClassVar[bytes] = b"oDAT"


@dataclass(frozen=True)
class NoisChunk:
    """Currently not used."""

    type_: ClassVar[bytes] = b"nOIS"


@dataclass(frozen=True)
class ExtrChunk:
    """Currently not used."""

    type_: ClassVar[bytes] = b"eXTR"


@dataclass(frozen=True)
class PcexChunk:
    """Currently not used."""

    type_: ClassVar[bytes] = b"pCEX"

@dataclass(frozen=True)
class BlinChunk:
    """Currently not used."""

    type_: ClassVar[bytes] = b"bLIN"


@dataclass(frozen=True)
class RtraChunk:
    """Currently not used."""

    type_: ClassVar[bytes] = b"rTRA"

@dataclass(frozen=True)
class MinfChunk:
    """Currently not used."""

    type_: ClassVar[bytes] = b"mINF"
