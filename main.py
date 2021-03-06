from pcaspy import SimpleServer, Driver
from utils import generate_pvdb, get_ip, get_index_and_address
import threading
import pyads
import logging
pvdb = {}


class myDriver(Driver):
    def __init__(self, plc):
        Driver.__init__(
            self,
        )
        self.tid = None
        self.plc = plc
        # todo start a thread here that stores the pv values by either:
        # - setting up callbacks for each read pv OR
        # - polling every 0.5s with a "multiple ads var" query (CANNOT BE DONE CURRENTLY, PYADS ONLY ACCEPTS READMULT BY NAME NOT ADDRESS
        # either of the above would be more efficient than polling every ADS var individually

    def read(self, reason):
        address, indexgrp, plctype = get_index_and_address(pvdb, reason)
        try:
            var = self._plc_read(address, indexgrp, plctype)
            if var is not None:
                return var
            else:
                logging.error(f"no value received for {reason}: {var}")
        except pyads.ADSError as e:
            logging.error(e)
            return 0

    def _plc_read(self, address, indexgrp, plctype):
        return self.plc.read(indexgrp, address, plc_datatype=plctype)

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
            address, indexgrp, plctype = get_index_and_address(pvdb, pv_name)
            self.plc.write(indexgrp, address, ads_value, plctype)
        except pyads.ADSError as e:
            logging.error(e)
        self.updatePVs()
        self.tid = None


logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s: %(message)s')
# todo we should generate this rather than rely on tcioc to do it
# todo get this from the macro instead
with open("tc_project_app.db") as db_file:
    contents = db_file.read()
    plc_ip, plc_port = get_ip(contents)
    generate_pvdb(pvdb, contents)

# This program takes a db file generated by tcioc (for now) and loads it into the db
plc = pyads.Connection(plc_ip, plc_port)
plc.open()

# todo we should do this to allow this to work alongside tcioc using
#  accesssecurity or a shared channelaccess
#  https://github.com/ISISComputingGroup/EPICS-refl/blob/master/reflectometry_server.py
server = SimpleServer()
prefix = ""  # blank, as the prefix is already burned into the pv name by tcioc
server.createPV(prefix, pvdb)
logging.info(f"created {len(pvdb)} PVs:")
for pv in pvdb.keys():
    logging.info(pv)
driver = myDriver(plc)

# process CA transactions
while True:
    server.process(0.1)
