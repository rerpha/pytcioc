from typing import List, Dict
import pyads

from constants import (
    SCAN_SECONDS,
)


def generate_pvdb(pvdb: Dict, symbols, enums: List[str]):
    for pvname, symbol in symbols.items():
        if pvname in enums:
            ads_type = pyads.PLCTYPE_INT
        else:
            ads_type = symbol.plc_type

        if ads_type in [pyads.PLCTYPE_INT, pyads.PLCTYPE_BOOL]:
            pcaspy_dtype = "int"
        else:
            pcaspy_dtype = "float"

        pvdb[pvname] = {
            "type": pcaspy_dtype,
            "scan": SCAN_SECONDS,
            "asyn": True,
            "adsvar": symbol.name,
            "adstype": ads_type,
        }
