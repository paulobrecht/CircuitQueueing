#!/usr/bin/python3

# IMPORT
import RPi.GPIO as gpio
import time
import sys
import os
from local_functions import logfunc

# mapping 0/1 to OFF/ON
map = {0:"OFF", 1:"ON"}

# log file
logloc = os.environ['CURB_LOCAL_LOG_LOC']
now = time.strftime("%H:%M:%S", time.localtime())

# get command line arg (ON or OFF)
try:
  arg1 = sys.argv[1]
except IndexError:
  log.write(now + ": Usage: 'python3 flipRelayWH.py OFF' or 'python3 flipRelayWH.py ON'.\n")
  raise SystemExit("Usage: 'python3 flipRelayWH.py OFF' or 'python3 flipRelayWH.py ON'.")
else:
  arg1 = arg1.upper() # case-insensitive
  if arg1 not in ["OFF", "ON"]:
    log.write(now + ": ERROR. Provided invocation argument " + arg1 + " is invalid. Specify only OFF or ON.\n")
    raise SystemExit("ERROR: Provided invocation argument " + arg1 + " is invalid. You must specify either OFF or ON.")
  else:
    flip = (arg1=="ON") * 1

# Assign GPIO pins for each water heater
# (we don't flip pool pump in this program)
WH_north = 11
WH_south = 13

# Set mode to BOARD to refer to Pi pin numbers
gpio.setwarnings(False)
gpio.setmode(gpio.BOARD)

# Set two pins (one for each device) as output
gpio.setup(WH_north,gpio.OUT)
gpio.setup(WH_south,gpio.OUT)

# get current WH status
WHN_status = [gpio.input(WH_north)]
WHS_status = [gpio.input(WH_south)]

# flip relay to off or on depending on command line arg supplied to script on crontab
# When turning OFF, turn both off. When turning on, turn on only North pump -- queryCurb will turn everything else on if North doesn't need to run right now
if flip == 1:
  gpio.output(WH_north,1)
  gpio.output(WH_south,0)
elif flip == 0:
  gpio.output(WH_north,0)
  gpio.output(WH_south,0)

# log action
WHN_status.append(gpio.input(WH_north))
WHS_status.append(gpio.input(WH_south))

a = "->"
N = [map[WHN_status[0]], map[WHN_status[1]]]
S = [map[WHS_status[0]], map[WHS_status[1]]]

message = "flipRelayWH changed status. North: " + N[0] + a + N[1] + ", South: " + S[0] + a + S[1] + ", Pool Pump: " +  P[0] + a + P[1]
logfunc(time=now, logloc=logloc, line=message)
