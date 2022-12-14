from pcaspy import SimpleServer, Driver
from utils import generate_pvdb
import threading
import pyads
import logging
from constants import AXIS_STRUCT

pvdb = {}


class myDriver(Driver):
    def __init__(self, plc):
        Driver.__init__(
            self,
        )
        self.plc = plc
        # todo start a thread here that stores the pv values by either:
        # - setting up callbacks for each read pv OR
        # - polling every 0.5s with a "multiple ads var" query (CANNOT BE DONE CURRENTLY, PYADS ONLY ACCEPTS READMULT BY NAME NOT ADDRESS
        # either of the above would be more efficient than polling every ADS var individually

    def read(self, reason):
        # print(f"got read for {reason}")
        try:
            pv = pvdb[reason]
            adstype = pv["adstype"]
            adsname = pv["adsvar"]
            symbol = pv["symbol"]
            if symbol is not None:
                var = symbol.read()
            else:
                # enum, try and read int instead
                var = self.plc.read_by_name(adsname, plc_datatype=pyads.PLCTYPE_INT)
            if var is not None:
                return var
            else:
                logging.error(f"no value received for {reason}: {var}")
        except pyads.ADSError as e:
            logging.error(e)
            return 0

    def write(self, reason, value):
        print(f"got write for {reason} val {value}")
        status = True
        # take proper actions
        pv_name = reason
        self.updatePVs()
        # run shell
        try:
            pv = pvdb[pv_name]
            adstype = pv["adstype"]
            adsname = pv["adsvar"]
            symbol = pv["symbol"]
            if symbol is not None:
                symbol.write(value)
            else:
                self.plc.write_by_name(adsname, value, plc_datatype=pyads.PLCTYPE_INT)
            print(f"wrote {value} to {adsname}")
        except pyads.ADSError as e:
            logging.error(e)
            status = False
        self.updatePVs()
        # store the values
        if status:
            self.setParam(reason, value)
        return status


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
plc = pyads.Connection("127.0.0.1.1.1", 852)
plc.open()

axes_num = plc.read_by_name("GVL_APP.nAXIS_NUM")  # TODO: make this a PV
logging.info(f"number of axes: {axes_num}")

symbols = {}
enums = {}
for i in range(1, axes_num + 1):
    for var, adsaddr in AXIS_STRUCT.items():
        full_pv_name = "TC_01:" + var.format(i)
        removed_prefix = var.split(":")[-1].replace("-", ".")[2:]
        split_by_dot = removed_prefix.split(".")
        first = "st" + split_by_dot[0].title()
        second_first_char = split_by_dot[1][0].lower()
        if adsaddr is not None:
            second = second_first_char + adsaddr
        else:
            # If none, we can just guess what the ADS vars name will be by stripping the
            # first char and converting to title case
            second = second_first_char + split_by_dot[1][1:].title()
        full = f"GVL.astAxes[{i}].{first}.{second}"
        if second_first_char == "e":
            enums[full_pv_name] = full
        else:
            try:
                val = plc.get_symbol(full, auto_update=True)
                symbols[full_pv_name] = val

            except Exception as e:
                print(f"{full} didn't work: {e}")


generate_pvdb(pvdb, symbols, enums)

# # todo we should do this to allow this to work alongside tcioc using
# #  accesssecurity or a shared channelaccess
# #  https://github.com/ISISComputingGroup/EPICS-refl/blob/master/reflectometry_server.py
server = SimpleServer()
prefix = (
    "TE:NDW1836:"  # blank, as the prefix is already burned into the pv name by tcioc
)
server.createPV(prefix, pvdb)
logging.info(f"created {len(pvdb)} PVs:")
for pv in pvdb.keys():
    logging.info(pv)
driver = myDriver(plc)

# process CA transactions
while True:
    server.process(0.1)
