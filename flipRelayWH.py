#!/usr/bin/python3

# IMPORT
import RPi.GPIO as gpio
import time
import sys

# mapping 0/1 to OFF/ON
map = {0:"OFF", 1:"ON"}

# log file
logloc = "/home/pi/CurbAPI/activity_log.txt"
now = time.strftime("%H:%M:%S", time.localtime())
log = open(logloc, "a")

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
# (We are using 2 and 4 for voltage)
WH_north = 11
WH_south = 13

# Set mode to BOARD to refer to Pi pin numbers
gpio.setwarnings(False)
gpio.setmode(gpio.BOARD)

# Set two pins (one for each device) as output
gpio.setup(WH_north,gpio.OUT)
gpio.setup(WH_south,gpio.OUT)

# flip relay to off or on depending on command line arg supplied to script on crontab
WHN_status = [None for x in range(2)]
WHS_status = [None for x in range(2)]
WHN_status[0] = gpio.input(WH_north)
WHS_status[0] = gpio.input(WH_south)

# When turning OFF, turn both off. When turning on, turn on only North to avoid both running for 1 minute
if flip==1:
  gpio.output(WH_north,1)
  gpio.output(WH_south,0)
elif flip==0:
  gpio.output(WH_north,0)
  gpio.output(WH_south,0)

# log action
WHN_status[1] = gpio.input(WH_north)
WHS_status[1] = gpio.input(WH_south)

log.write(now + ": flipRelayWH changed status of water heaters. North: " + map[WHN_status[0]] + "->" + map[WHN_status[1]] + ", South: " + map[WHS_status[0]] + "->" + map[WHS_status[1]] + ".\n")

log.close()
