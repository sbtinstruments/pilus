from dataclasses import dataclass

from ..formats import register_parsers, wave


@dataclass(frozen=True)
class Wave:
    """Linear pulse-code modulated (LPCM) signal stored in memmory."""

    byte_depth: int
    time_step_ns: int
    data: bytes = bytes()

    def __post_init__(self) -> None:
        if len(self.data) % self.byte_depth != 0:
            raise ValueError("Data length must be a multiple of the byte depth.")

    def __len__(self) -> int:
        """Return the logical length of this wave.

        Logical, in the sense that it takes the byte depth into account.
        I.e., it's not just the raw byte count.
        """
        return len(self.data) // self.byte_depth


register_parsers("audio/vnd.wave", from_io=lambda io: wave.from_io(Wave, io))
