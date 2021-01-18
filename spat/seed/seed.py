import logging
from dataclasses import dataclass
from datetime import datetime
from typing import DefaultDict, Iterable, Union


logging.debug("cica")

@dataclass(frozen=True)
class Seed:
    """Signal data objectn."""
    # time_step: float
    # interval #type: datetime.interval
    time: list
    data: DefaultDict #Mapping[site,frequency]

    @classmethod
    def from_dict(cls, raw_iqs: dict):
        time = time=raw_iqs['data']['site0']['hf']['time']
        myqs = raw_iqs
        for __, site in myqs['data'].items():
            for __, freq in site.items():
                del freq['time']
        
        return cls(time, myqs['data'])
        pass

    def __str__(self):
        return 'cica'

    def __repr__(self):
        return "Seed object\n.time,\n.data:"+_tree_string(self.data)


def _tree_string(data:Union[dict,DefaultDict], level=0) -> str:
    """String nested stucture overview."""
    out_str = ""
    for key, value in data.items():
        out_str = out_str + "\n" + level*"  " + key
        if isinstance(value,dict):
            out_str = out_str + ":"
            out_str = out_str + _tree_string(value,level=level+1)
    return out_str
