from datetime import datetime

from ..formats import register_parsers
from ..model import Model


class WaveMeta(Model):
    start_time: datetime
    max_value: int


register_parsers(
    "application/vnd.sbt.wave-meta+json",
    from_data=WaveMeta.from_json_data,
)
