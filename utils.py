from typing import List, Dict
import pyads

from constants import (
    SCAN_SECONDS,
)


def generate_pvdb(pvdb: Dict, symbols, enums: Dict[str, str]):
    for pvname, symbol in symbols.items():
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
            "symbol": symbol,
        }

    for pvname, ads_var in enums.items():
        ads_type = pyads.PLCTYPE_INT
        pvdb[pvname] = {
            "type": "int",
            "scan": SCAN_SECONDS,
            "asyn": True,
            "adsvar": ads_var,
            "adstype": ads_type,
            "symbol": None,
        }
