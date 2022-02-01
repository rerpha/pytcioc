from typing import Tuple, List, Dict

from constants import (
    SCAN_SECONDS,
    epics_to_pcas_type_mapping,
    epics_to_ads_type_mapping,
)


def get_index_and_address(pvdb: Dict, reason: str):
    indexgrp = pvdb[reason]["adsindex_group"]
    address = pvdb[reason]["adsaddress"]
    plctype = pvdb[reason]["adstype"]
    return address, indexgrp, plctype


def generate_pvdb(pvdb: Dict, file_str: str):
    records = file_str.split("}")
    for record_def in records:
        index_group = ""
        address = ""
        pvname = ""
        pcaspy_dtype = ""
        ads_type = ""
        lines = split_up_record_lines(record_def)
        for line in lines:
            (key, value) = line.split(",")
            if (
                key in epics_to_pcas_type_mapping.keys() and key != "mbbo"
            ):  # Todo handle enums.. if we need to?
                # this is the first line therefore must contain the name
                ads_type, pcaspy_dtype = get_datatypes(key)
                pvname = value
            elif key == "OUT":
                # this is the OUT field which specifies comms info
                address, index_group = get_comms_info(value)
        if all([ads_type, index_group, address, pcaspy_dtype]):
            pvdb[pvname] = {
                "type": pcaspy_dtype,
                "scan": SCAN_SECONDS,
                "asyn": True,
                "adsindex_group": index_group,
                "adsaddress": address,
                "adstype": ads_type,
            }


def get_datatypes(epics_datatype: str):
    pcasdtype = epics_to_pcas_type_mapping[epics_datatype]
    ads_type = epics_to_ads_type_mapping[epics_datatype]
    return ads_type, pcasdtype


def split_up_record_lines(recorddef: str) -> List[str]:
    """
    Splits up record lines and removes unneeded characters.
    :param recorddef: the full record definition
    :return: a list of all of the lines in the record definition
    """
    lines = (
        recorddef.lstrip("\n")
        .replace("{", "")
        .replace(" ", "")
        .replace('"', "")
        .replace("'", "")
        .replace("\t", "")
        .replace("field(", "")
        .replace("record(", "")
        .replace(")", "")
        .split("\n")
    )  # todo do this with re.sub instead
    # remove empty elements with filter()
    return list(filter(None, lines))


def get_comms_info(value: str) -> Tuple[int, int]:
    fqname = value.lstrip("@tc://")
    split_addr = fqname.split("/")
    index_group = split_addr[1]  # index 0 is the ip:port
    (address, data_size) = split_addr[2].split(":")
    return int(address), int(index_group)


def get_ip(file_str: str) -> Tuple[str, int]:
    test = file_str.split("@tc://")[1].split("/")[0]
    (ip, port) = test.split(":")
    return ip, int(port)


def get_all_addresses(pvdb: Dict):
    for address, indexgrp, plctype in [
        get_index_and_address(pvdb, pvname) for pvname in pvdb.keys()
    ]:
        print(address, indexgrp, plctype)
