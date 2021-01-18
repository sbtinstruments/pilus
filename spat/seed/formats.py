from spat.seed._format_utils import _get_file_size, _read_signature, _write_signature, read_uint32, _read_chunk_type, _read_sysi, _write_sysi, _read_ihdr, _write_ihdr, _read_idat, _write_idat, _parse_iqs_channels


def from_iqs():
    """Create Seed from iqs file."""
    print("from iqs")




def open_iqs(file_name: str):
    """Read V2 IQS file."""
    iqs:dict = {}
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
                iqs["IHDR"] = _read_ihdr(f)
            elif chunk_type == 'IDAT':
                iqs["IDAT"].append(_read_idat(f,iqs["IHDR"]))
            else:
                f.seek(chunk_length+4)
                Warning('Unknown chunk type. Skipping.')
                pass # error

    _parse_iqs_channels(iqs)
    return iqs

def write_iqs(iqs, file_name: str) -> bool:
    """Write v2.0 iqs file."""
    with open(file_name, 'w+b') as f:
        _write_signature(f)
        _write_sysi(f, iqs)
        _write_ihdr(f, iqs)
        _write_idat(f, iqs)
        
    return True