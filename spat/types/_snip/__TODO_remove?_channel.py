from dataclasses import dataclass

from immutables import Map


@dataclass(frozen=True)
class Channel:
    byte_depth: int
    max_value: int
    data: bytes

    def __post_init__(self) -> None:
        if len(self.data) % self.byte_depth != 0:
            raise ValueError("Data length must be a multiple of the byte depth.")

    def __len__(self) -> int:
        """Return the logical length of this channel.

        Logical, in the sense that it takes the byte depth into account.
        I.e., it's not just the raw byte count.
        """
        return len(self.data) // self.byte_depth


ChannelMap = Map[str, Channel]
