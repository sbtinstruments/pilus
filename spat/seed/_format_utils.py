import json
from collections import defaultdict
from dataclasses import dataclass
from itertools import repeat
from pathlib import Path
from typing import DefaultDict, Iterable, Union, IO

import numpy as np  # type: ignore

# inspired by: https://stackoverflow.com/a/8702435
nested_dict = lambda: defaultdict(nested_dict) # type: ignore

def remove_termination(str:str, terminating_char='\x00'):
    return str[:str.index(terminating_char)]

def _read_chunk_type(f):
    """Read the 4 byte long chunk ID"""
    # side effect of moving file pointer
    return f.read(4).decode('utf-8')

def read_uint8(f):
    return int.from_bytes(f.read(1), byteorder='little', signed=False)

def write_uint8(f, val:int):
    return f.write(val.to_bytes(1, byteorder='little', signed=False))

def read_uint32(f):
    return int.from_bytes(f.read(4), byteorder='little', signed=False)

def write_uint32(f, val:int):
    return f.write(val.to_bytes(4, byteorder='little', signed=False))

def read_uint64(f):
    return int.from_bytes(f.read(8), byteorder='little', signed=False)

def write_uint64(f, val:int):
    return f.write(val.to_bytes(8, byteorder='little', signed=False))

def read_int8(f):
    return int.from_bytes(f.read(1), byteorder='little', signed=True)

def read_int16(f):
    return int.from_bytes(f.read(2), byteorder='little', signed=True)

def read_int32(f):
    return int.from_bytes(f.read(4), byteorder='little', signed=True)

def read_int64(f):
    return int.from_bytes(f.read(8), byteorder='little', signed=True)

def write_int8(f, val:int):
    return f.write(val.to_bytes(1, byteorder='little', signed=True))

def write_int16(f, val:int):
    return f.write(val.to_bytes(2, byteorder='little', signed=True))

def write_int32(f, val:int):
    return f.write(val.to_bytes(4, byteorder='little', signed=True))

def write_int64(f, val:int):
    return f.write(val.to_bytes(8, byteorder='little', signed=True))


def _read_signature(f):
    """Read IQS v2 signature."""
    return bytes.hex(f.read(8))

def _write_signature(f,sign='894951530d0a1a0a'):
    """Write IQS v2 signature."""
    return f.write(bytes.fromhex(sign))

def _get_file_size(file_name:str):
    return Path(file_name).stat().st_size

def _read_sysi(f, chunk_length):
    info = json.loads(f.read(chunk_length)) # python3.9: encoding arg removed
    crc = read_uint32(f) # TODO: move crc check into fnc decorator
    return info

def _write_sysi(f, iqs:dict) -> None:
    """Write system information."""
    sys_info = bytes(json.dumps(iqs['sys_info']).replace(" ",""),'utf-8')
    byte_length = len(sys_info)
    write_uint32(f, byte_length)
    f.write(b'sYSI')
    f.write(sys_info)
    # write crc
    write_uint32(f,0)

def _read_ihdr(f):
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

def _write_ihdr(f, iqs:dict) -> None:
    """Write header chunk."""
    # write chunk length
    write_uint32(f, _get_ihdr_b_length(iqs))
    # write chunk type
    f.write(b'IHDR')
    # write nSites
    write_uint32(f, len(iqs['IHDR'].keys()))
    for site_name, site in iqs['IHDR'].items():
        # write site name
        b_site_name = bytearray(site_name,'utf-8')
        f.write(b_site_name + bytearray(256 - len(b_site_name)))
        # write nChannels
        write_uint32(f, len(site.keys()))
        for freq_name, freq in site.items():
            # write freq name
            b_freq_name = bytearray(freq_name,'utf-8')
            f.write(b_freq_name + bytearray(256 - len(b_freq_name)))
            write_uint32(f, freq["sample_time_step"])
            write_uint8(f, freq["sample_byte_depth"])
            write_int64(f, freq["sample_max_signal_amplitude"])
            # HACK: write some bytes to comply with the specs
            f.write(bytearray(56))

    # write crc
    write_uint32(f,0)

def _get_ihdr_b_length(iqs:dict) -> int:
    """Compute IHDR chunk byte length."""
    site_names = list(iqs['IHDR'].keys())
    n_sites = len(site_names)
    n_channels = len(iqs['IHDR'][site_names[0]].keys())
    return n_sites*(256+4+n_channels*(256 + 4 + 1 + 8 + 56))+4

def _get_shdr_b_length() -> int:
    """Return SHDR chunk byte length."""
    return 8

def _write_shdr(f, iqs:dict) -> None:
    """Write legacy header chunk."""
    # write chunk length
    write_uint32(f, _get_shdr_b_length())
    # write chunk type
    f.write(b'SHDR')
    # write time step
    write_uint32(f, iqs["SHDR"]["sample_time_step"])
    # write max amplitude (scaling)
    write_uint32(f, iqs["SHDR"]["sample_max_signal_amplitude"])
    # write crc
    write_uint32(f,0)

def _read_idat(f, ihdr: Union[dict, DefaultDict]):
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
            
            idat_segment[site][channel]["re"] = np.array([_read_int_func(f) for i in repeat(None, _n_samples)])
            idat_segment[site][channel]["im"] = np.array([_read_int_func(f) for i in repeat(None, _n_samples)])


    crc = read_uint32(f) # TODO: move crc check into fnc decorator  #pylint: disable=unused-variable
    return idat_segment


def _write_idat(f, iqs) -> None:
    """Write IDAT chunks."""
    for chunk in iqs['IDAT']:
        # write chunk length
        write_uint32(f, _get_idat_b_length(chunk))
        # write chunk type
        f.write(b'IDAT')
        # write timestamp
        write_uint64(f, chunk['timestamp'])
        # write duration
        write_uint64(f, chunk['duration'])
        # write data chunks
        for site_name, site in chunk.items():
            if type(site) is not defaultdict: continue
            for channel_name, channel in site.items():
                _byte_depth = iqs['IHDR'][site_name][channel_name]["sample_byte_depth"]
                if _byte_depth == 1:
                    _write_int_func = write_int8
                elif _byte_depth == 4:
                    _write_int_func = write_int32
                elif _byte_depth == 8:
                    _write_int_func = write_int64
                else:
                    _write_int_func = write_int16

                [_write_int_func(f, data.item()) for data in channel['re']]
                [_write_int_func(f, data.item()) for data in channel['im']]

        # write crc
        write_uint32(f,0)


def _get_idat_b_length(idat:dict) -> int:
    """Compute IDAT chunk byte length."""
    # TODO: remove hard-coded site/channel/re/im names
    return ((len(idat['site0']['hf']['re']) * 4) * 4 + 8)*2

def _write_sdat(f, iqs) -> None:
    """Write SDAT chunks."""
    for chunk in iqs['SDAT']:
        # write chunk length
        write_uint32(f, _get_sdat_b_length(chunk))
        # write chunk type
        f.write(b'SDAT')
        # write timestamp
        write_uint64(f, chunk['timestamp'])
        # write data chunks
        for values in zip(chunk["hf_re"], chunk["hf_im"], chunk["lf_re"], chunk["lf_im"]):
            for value in values:
                # .item() converts numpy types to native types
                write_int32(f, value.item())

        # write crc
        write_uint32(f,0)

def _get_sdat_b_length(chunk:dict) -> int:
    """Compute SDAT chunk byte length."""
    return ((len(chunk["hf_re"]) * 4) * 4 + 8)



def _parse_iqs_channels(iqs:Union[dict,DefaultDict]):
    """Parse raw .iqs data 'IDAT' into easy-to-handle lists."""
    data = nested_dict()

    for segment in iqs['IDAT']:
        for site_key, site in segment.items():
            try:
                for ch_key, channel in site.items():
                    for imre_key, imre_data  in channel.items():
                        try:
                            data[site_key][ch_key][imre_key] += np.hstack(data[site_key][ch_key][imre_key], imre_data)
                        except TypeError:
                            data[site_key][ch_key][imre_key] = imre_data
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
            channel['time'] = np.array([(start_time + x*time_step)/1e6 for x in range(0, n_data)])
        


