import pyads

SCAN_SECONDS = 1
epics_to_pcas_type_mapping = {
    "bo": "int",
    "longout": "int",
    "ao": "int",
    "mbbo": "enum",
}
epics_to_ads_type_mapping = {
    "bo": pyads.PLCTYPE_BOOL,
    "longout": pyads.PLCTYPE_INT,
    "ao": pyads.PLCTYPE_LREAL,
    "mbbo": "enum",
}
