from datetime import datetime

from ..model import Model, add_media_type


@add_media_type("application/vnd.sbt.wave-meta+json")
class WaveMeta(Model):
    start_time: datetime
    max_value: int