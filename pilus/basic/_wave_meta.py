from datetime import datetime

from ..model import Model, add_media_type


@add_media_type("application/vnd.sbt.wave-meta+json")
class WaveMeta(Model):
    """Metadata for a wave (LPCM signal)."""

    start_time: datetime
    max_amplitude: int
