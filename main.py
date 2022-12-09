from pcaspy import SimpleServer, Driver
from utils import generate_pvdb
import threading
import pyads
import logging
from constants import AXIS_STRUCT

pvdb = {}


# class myDriver(Driver):
#     def __init__(self, plc):
#         Driver.__init__(
#             self,
#         )
#         self.tid = None
#         self.plc = plc
#         # todo start a thread here that stores the pv values by either:
#         # - setting up callbacks for each read pv OR
#         # - polling every 0.5s with a "multiple ads var" query (CANNOT BE DONE CURRENTLY, PYADS ONLY ACCEPTS READMULT BY NAME NOT ADDRESS
#         # either of the above would be more efficient than polling every ADS var individually
#
#     def read(self, reason):
#         address, indexgrp, plctype = get_index_and_address(pvdb, reason)
#         try:
#             var = self._plc_read(address, indexgrp, plctype)
#             if var is not None:
#                 return var
#             else:
#                 logging.error(f"no value received for {reason}: {var}")
#         except pyads.ADSError as e:
#             logging.error(e)
#             return 0
#
#     def _plc_read(self, address, indexgrp, plctype):
#         return self.plc.read(indexgrp, address, plc_datatype=plctype)
#
#     def write(self, reason, value):
#         status = True
#         # take proper actions
#         pv_name = reason
#         if not self.tid:
#             self.tid = threading.Thread(
#                 target=self.write_to_beckhoff,
#                 args=(
#                     pv_name,
#                     value,
#                 ),
#             )
#             self.tid.start()
#         else:
#             status = False
#         # store the values
#         if status:
#             self.setParam(reason, value)
#         return status
#
#     def write_to_beckhoff(self, pv_name, ads_value):
#         self.updatePVs()
#         # run shell
#         try:
#             address, indexgrp, plctype = get_index_and_address(pvdb, pv_name)
#             self.plc.write(indexgrp, address, ads_value, plctype)
#         except pyads.ADSError as e:
#             logging.error(e)
#         self.updatePVs()
#         self.tid = None


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
plc = pyads.Connection("127.0.0.1.1.1", 852)
plc.open()

axes_num = plc.read_by_name("GVL_APP.nAXIS_NUM")  # TODO: make this a PV
logging.info(f"number of axes: {axes_num}")


symbols = {}
enums = []
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
            enums.append(full)
            val = plc.get_symbol(full, plc_datatype=pyads.PLCTYPE_INT)
            symbols[full_pv_name] = val
        else:
            try:
                val = plc.get_symbol(full, auto_update=True)
                symbols[full_pv_name] = val

            except Exception as e:
                enums.append(f"{full} didn't work: {e}")

# for key, val in symbols.items():
#     if val.name in enums:
#         ads_val = plc.read_by_name(val.name, pyads.PLCTYPE_INT)
#     else:
#         ads_val = val.read()
#
#     print(f"{key} is {ads_val}")

generate_pvdb(pvdb, symbols, enums)
#
# for i in AXIS_STRUCT:
#
# # todo we should do this to allow this to work alongside tcioc using
# #  accesssecurity or a shared channelaccess
# #  https://github.com/ISISComputingGroup/EPICS-refl/blob/master/reflectometry_server.py
# server = SimpleServer()
# prefix = ""  # blank, as the prefix is already burned into the pv name by tcioc
# server.createPV(prefix, pvdb)
# logging.info(f"created {len(pvdb)} PVs:")
# for pv in pvdb.keys():
#     logging.info(pv)
# # driver = myDriver(plc)
#
# # process CA transactions
# while True:
#     server.process(0.1)
