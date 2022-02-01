from typing import Tuple
from pcaspy import Driver, SimpleServer
import pyads
import threading

prefix = ""
pvdb = {}
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


def get_index_and_address(reason):
    indexgrp = int(pvdb[reason]["adsindex_group"])
    address = int(pvdb[reason]["adsaddress"])
    plctype = pvdb[reason]["adstype"]
    return address, indexgrp, plctype


class myDriver(Driver):
    def __init__(self, plc):
        Driver.__init__(
            self,
        )
        self.tid = None
        self.plc = plc

    def read(self, reason):
        address, indexgrp, plctype = get_index_and_address(reason)
        try:
            var = self.plc.read(indexgrp, address, plc_datatype=plctype)
            return var
        except pyads.ADSError as e:
            print(e)

    def write(self, reason, value):
        status = True
        # take proper actions
        pv_name = reason
        if not self.tid:
            self.tid = threading.Thread(
                target=self.write_to_beckhoff,
                args=(
                    pv_name,
                    value,
                ),
            )
            self.tid.start()
        else:
            status = False
        # store the values
        if status:
            self.setParam(reason, value)
        return status

    def write_to_beckhoff(self, pv_name, ads_value):
        self.updatePVs()
        # run shell
        try:
            address, indexgrp, plctype = get_index_and_address(pv_name)
            self.plc.write(indexgrp, address, ads_value, plctype)
        except pyads.ADSError as e:
            print(e)
        self.updatePVs()
        self.tid = None


def generate_pvdb(file_str: str):
    records = file_str.split("}")
    for recorddef in records:
        index_group = ""
        address = ""
        pvname = ""
        pcasdtype = ""
        ads_type = ""
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
        )
        for line in lines:
            if line:
                (key, value) = line.split(",")
                if key in epics_to_pcas_type_mapping.keys() and key != "mbbo":
                    # this is the first line
                    epicsdatatype = key
                    pcasdtype = epics_to_pcas_type_mapping[epicsdatatype]
                    ads_type = epics_to_ads_type_mapping[epicsdatatype]
                    pvname = value
                elif key == "OUT":
                    fqname = value.lstrip("@tc://")
                    split_addr = fqname.split("/")
                    index_group = split_addr[1]  # index 0 is the ip:port
                    (address, data_size) = split_addr[2].split(":")
        if all([ads_type, index_group, address, pcasdtype]):
            pvdb[pvname] = {
                "type": pcasdtype,
                "scan": SCAN_SECONDS,
                "asyn": True,
                "adsindex_group": index_group,
                "adsaddress": address,
                "adstype": ads_type,
            }


def get_ip(file_str: str) -> Tuple[str, int]:
    test = file_str.split("@tc://")[1].split("/")[0]
    (ip, port) = test.split(":")
    return ip, int(port)


if __name__ == "__main__":
    with open("tc_project_app.db") as db_file:
        contents = db_file.read()
        plc_ip, plc_port = get_ip(contents)
        generate_pvdb(contents)

    # This program takes a db file generated by tcioc (for now) and loads it into the db
    plc = pyads.Connection(plc_ip, plc_port)
    plc.open()

    server = SimpleServer()
    server.createPV(prefix, pvdb)
    print(f"created PVs: {pvdb.keys()}")
    driver = myDriver(plc)

    # process CA transactions
    while True:
        server.process(0.1)
