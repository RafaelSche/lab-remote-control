from lab_remote_control.devices.dab import DualActiveBridge
from serial import Serial
from time import sleep
import sys

if len(sys.argv) > 2:
    clear_mc_buffer = True
else:
    clear_mc_buffer = False

dab = DualActiveBridge(Serial('/dev/ttyUSB0'), clear_mc_buffer=clear_mc_buffer)
if clear_mc_buffer:
    sleep(0.6)
dab.set_phase(int(sys.argv[1]))
del dab
