from pathlib import Path
from itertools import repeat
from collections import defaultdict
import json
from typing import Union,DefaultDict

nested_dict = lambda: defaultdict(nested_dict) # inspired by: https://stackoverflow.com/a/8702435

def remove_termination(str:str, terminating_char='\x00'):
    return str[:str.index(terminating_char)]

def _read_chunk_type(f):
    """Read the 4 byte long chunk ID"""
    # side effect of moving file pointer
    return f.read(4).decode('utf-8')

def read_uint8(f):
    return int.from_bytes(f.read(1), byteorder='little', signed=False)

def read_uint32(f):
    return int.from_bytes(f.read(4), byteorder='little', signed=False)

def read_uint64(f):
    return int.from_bytes(f.read(8), byteorder='little', signed=False)

def read_int8(f):
    return int.from_bytes(f.read(1), byteorder='little', signed=True)

def read_int16(f):
    return int.from_bytes(f.read(2), byteorder='little', signed=True)

def read_int32(f):
    return int.from_bytes(f.read(4), byteorder='little', signed=True)

def read_int64(f):
    return int.from_bytes(f.read(8), byteorder='little', signed=True)

def _read_signature(f):
    return bytes.hex(f.read(8))

def _get_file_size(file_name:str):
    return Path(file_name).stat().st_size

def _read_sysi(f, chunk_length):
    info = json.loads(f.read(chunk_length)) # python3.9: encoding arg removed
    crc = read_uint32(f) # TODO: move crc check into fnc decorator
    return info

def _read_IHDR(f):
    n_sites = read_uint32(f)
    ihdr = nested_dict()
    for i in repeat(None, n_sites):                   #pylint: disable=unused-variable
        _site_name = remove_termination(f.read(256).decode('utf-8')) # site0/1
        n_channels = read_uint32(f)
        for j in repeat(None, n_channels):          #pylint: disable=unused-variable
            _sample_name = remove_termination(f.read(256).decode('utf-8')) #hf/lf
            ihdr[_site_name][_sample_name]["sample_time_step"] = read_uint32(f)
            ihdr[_site_name][_sample_name]["sample_byte_depth"] = read_uint8(f)
            # HACK: read int64 and skip the rest 56 bytes
            ihdr[_site_name][_sample_name]["sample_max_signal_amplitude"] = read_int64(f)
            f.seek(f.tell() + 56)

    
    crc = read_uint32(f) # TODO: move crc check into fnc decorator  #pylint: disable=unused-variable
    return ihdr

def _read_IDAT(f, ihdr: Union[dict, DefaultDict]):
    idat_segment = nested_dict()
    timestamp = read_uint64(f)
    idat_segment['timestamp'] = timestamp
    duration = read_uint64(f)
    idat_segment['duration'] = duration

    for site in ihdr.keys() :
        for channel in ihdr[site].keys():
            _n_samples = int(duration/ihdr[site][channel]["sample_time_step"])
            _byte_depth = ihdr[site][channel]["sample_byte_depth"]

            if _byte_depth == 1:
                _read_int_func = read_int8
            elif _byte_depth == 4:
                _read_int_func = read_int32
            elif _byte_depth == 8:
                _read_int_func = read_int64
            else:
                _read_int_func = read_int16
            
            idat_segment[site][channel]["re"] = [_read_int_func(f) for i in repeat(None, _n_samples)]
            idat_segment[site][channel]["im"] = [_read_int_func(f) for i in repeat(None, _n_samples)]


    crc = read_uint32(f) # TODO: move crc check into fnc decorator  #pylint: disable=unused-variable
    return idat_segment

def _parse_iqs_channels(iqs:Union[dict,DefaultDict]):
    """Parse raw .iqs data 'IDAT' into easy-to-handle lists."""
    data = nested_dict()

    for segment in iqs['IDAT']:
        for site_key, site in segment.items():
            try:
                for ch_key, channel in site.items():
                    for imre_key, imre_data  in channel.items():
                        try:
                            data[site_key][ch_key][imre_key] += imre_data
                        except TypeError:
                            data[site_key][ch_key][imre_key] = []
                            data[site_key][ch_key][imre_key] += imre_data
            except AttributeError:
                pass

    iqs['data'] = data
    # TODO: store only single time vector
    _add_time_vector(iqs)

def _add_time_vector(iqs:Union[dict,DefaultDict]):
    """Parse timestamp and timestep values into data timestamps."""
    # time values in ns
    start_times = [idat['timestamp'] for idat in iqs['IDAT']]
    t = 0
    for site_name , site in iqs['data'].items():
        for channel_name , channel in site.items():
            start_time = start_times[t]
            time_step = iqs['IHDR'][site_name][channel_name]['sample_time_step'] * 1e-3
            n_data = len(channel['re'])
            # divide with 1e6 so the time vector is in standard unix epoch format
            channel['time'] = [(start_time + x*time_step)/1e6 for x in range(0, n_data)]
        


def open_iqs(file_name: str):
    """Read V2 IQS file."""
    iqs = {}
    iqs["IDAT"] = []

    fileSize = _get_file_size(file_name)

    with open(file_name, 'r+b') as f:
        assert _read_signature(f) == '894951530d0a1a0a'

        while f.tell() != fileSize :
            chunk_length = read_uint32(f)
            chunk_type = _read_chunk_type(f)
            
            if chunk_type == 'sYSI':
                iqs["sys_info"] = _read_sysi(f, chunk_length)
            elif chunk_type == 'IHDR':
                iqs["IHDR"] = _read_IHDR(f)
            elif chunk_type == 'IDAT':
                iqs["IDAT"].append(_read_IDAT(f,iqs["IHDR"]))
            else:
                f.seek(chunk_length+4)
                Warning('Unknown chunk type. Skipping.')
                pass # error

    _parse_iqs_channels(iqs)
    return iqs










