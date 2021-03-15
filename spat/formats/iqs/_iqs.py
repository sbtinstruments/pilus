from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

from ...seed import Channel, ChannelMap, Seed
from ._utils import (
    _get_file_size,
    _parse_iqs_channels,
    _read_chunk_type,
    _read_idat,
    _read_ihdr,
    _read_signature,
    _read_sysi,
    _write_idat,
    _write_ihdr,
    _write_signature,
    _write_sysi,
    read_uint32,
)


def from_iqs():
    """Create Seed from iqs file."""
    print("from iqs")


def open_iqs(file_name: str):
    """Read V2 IQS file."""
    iqs: dict = {}
    iqs["IDAT"] = []

    fileSize = _get_file_size(file_name)

    with open(file_name, "r+b") as f:
        assert _read_signature(f) == "894951530d0a1a0a"

        while f.tell() != fileSize:
            chunk_length = read_uint32(f)
            chunk_type = _read_chunk_type(f)

            if chunk_type == "sYSI":
                iqs["sys_info"] = _read_sysi(f, chunk_length)
            elif chunk_type == "IHDR":
                iqs["IHDR"] = _read_ihdr(f)
            elif chunk_type == "IDAT":
                iqs["IDAT"].append(_read_idat(f, iqs["IHDR"]))
            else:
                f.seek(chunk_length + 4)
                Warning("Unknown chunk type. Skipping.")
                pass  # error

    _parse_iqs_channels(iqs)
    return iqs


def write_iqs(iqs, file_name: str) -> bool:
    """Write v2.0 iqs file."""
    with open(file_name, "w+b") as f:
        _write_signature(f)
        _write_sysi(f, iqs)
        _write_ihdr(f, iqs)
        _write_idat(f, iqs)

    return True


def load(file_path: Path, delimiter: str = "__") -> Seed:
    """Load IQS file into it's seed representation."""
    raw_iqs = open_iqs(str(file_path))
    for key, val in raw_iqs["data"]["site1"]["lf"].items():
        print(f"key:{key} type(val):{type(val)}")

    # TODO: Ensure that these values actually are the same across sites and channels.
    time_step_ns = raw_iqs["IHDR"]["site0"]["hf"]["time_step"]
    byte_depth = raw_iqs["IHDR"]["site0"]["hf"]["sample_byte_depth"]
    max_value = raw_iqs["IHDR"]["site0"]["hf"]["sample_max_signal_amplitude"]

    channels: Dict[str, Channel] = {}

    for site_name, site in raw_iqs["data"].items():
        for freq_name, freq in site.items():
            for part_name, part in freq.items():
                channel_name = delimiter.join((site_name, freq_name, part_name))
                print(f"== channel_name:{channel_name}")
                print(f"== channel:{part}")

                # channels[channel_name] = channel

    myqs = raw_iqs
    for __, site in myqs["data"].items():
        for __, freq in site.items():
            pass

    # time_step =

    return Seed(time_step_ns)
