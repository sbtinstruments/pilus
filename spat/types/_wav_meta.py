from datetime import datetime

from ..formats import register_parser
from ..formats.model import Model


class WavMeta(Model):
    start_time: datetime
    max_value: int


register_parser("application/vnd.sbt.wav-meta+json", WavMeta.from_json_data)
