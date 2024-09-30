from pydantic import AwareDatetime, PositiveInt

from ...forge import FORGE
from ...model import FrozenModel


@FORGE.register_model("application/vnd.sbt.wave-meta+json")
class WaveMeta(FrozenModel):
    """Metadata for a wave (LPCM signal)."""

    start_time: AwareDatetime
    max_amplitude: PositiveInt
