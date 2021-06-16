from spat.seed._format_utils import _get_file_size, _read_signature, _write_signature, read_uint32, _read_chunk_type, _read_sysi, _write_sysi, _read_ihdr, _write_ihdr, _read_idat, _write_idat, _parse_iqs_channels, _write_shdr, _write_sdat

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

def write_iqs_v1(iqs, file_name: str) -> bool:
    """Write v1.0 iqs file."""
    with open(file_name, 'w+b') as f:
        _write_signature(f)
        _write_sysi(f, iqs)
        _write_shdr(f, iqs)
        _write_sdat(f, iqs)
        
    return True

def to_IQSv1(iqs: dict, site=0) -> dict:
    """Cast IQSv2 dict to legacy IQSv1 format, keeping only one site"""
    res = dict()
    site_name = "site" + str(site)
    assert site_name == "site0" or site_name == "site1"
    res["sys_info"] = iqs["sys_info"]
    assert iqs["IHDR"][site_name]["lf"]["sample_time_step"] == iqs["IHDR"][site_name]["hf"]["sample_time_step"]
    assert iqs["IHDR"][site_name]["lf"]["sample_max_signal_amplitude"] == iqs["IHDR"][site_name]["hf"]["sample_max_signal_amplitude"]
    res["SHDR"] = { "sample_time_step": iqs["IHDR"][site_name]["hf"]["sample_time_step"], 
                    "sample_max_signal_amplitude": iqs["IHDR"][site_name]["hf"]["sample_max_signal_amplitude"]}
    res["SDAT"] = []
    for chunk in iqs["IDAT"]:
        sdat_chunk = dict()
        sdat_chunk["timestamp"] = chunk["timestamp"]
        sdat_chunk["hf_re"] = chunk[site_name]["hf"]["re"]
        sdat_chunk["hf_im"] = chunk[site_name]["hf"]["im"]
        sdat_chunk["lf_re"] = chunk[site_name]["lf"]["re"]
        sdat_chunk["lf_im"] = chunk[site_name]["lf"]["im"]
        res["SDAT"].append(sdat_chunk)
    return res
    
