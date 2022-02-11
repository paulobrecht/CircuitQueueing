#!/usr/bin/python3

# IMPORT
import os
import RPi.GPIO as gpio
import local_functions as LF
from time import strftime, localtime
from sys import argv

# log file
logloc = os.environ['CURB_LOCAL_LOG_LOC']


# to map ON/OFF to 1/0 from gpioMaps(), which goes the other way
def get_key(val):
    for key, value in gpioMaps()[1].items():
         if val == value:
             return key


# get command line arg (ON or OFF)
try:
  arg1 = argv[1]
except IndexError:
  LF.logFunc(logloc = logloc, line = "Usage: 'python3 flipRelayWH.py OFF' or 'python3 flipRelayWH.py ON'")
else:
  arg1 = arg1.upper() # case-insensitive
  if arg1 not in ["OFF", "ON"]:
    LF.logFunc(logloc = logloc, line = "ERROR. Provided invocation argument " + arg1 + " is invalid. Specify only OFF or ON.")

# GPIO setup
LF.gpioSetup()

# start list for each device that will be [before, after]
initial_dict = LF.gpioCheckStatus(["WH_north", "WH_south", "ppump"])
WHN_status = [initial_dict["WH_north"]]
WHS_status = [initial_dict["WH_south"]]
PP_status  = [initial_dict["ppump"]]

# flip relay to off or on depending on command line arg supplied to script on crontab
# When turning OFF, turn both off. When turning on, turn on only North pump -- queryCurb will turn everything else on if North doesn't need to run right now
if arg1 == "ON":
  LF.gpioSetStatus(status_dict = {"WH_north": 1, "WH_south": 1, "ppump": 1})
elif arg1 == "OFF":
  LF.gpioSetStatus(status_dict = {"WH_north": 0, "WH_south": 0})

# second item of each device status list
end_dict = LF.gpioCheckStatus(["WH_north", "WH_south", "ppump"])
WHN_status.append(end_dict["WH_north"])
WHS_status.append(end_dict["WH_south"])
PP_status.append(end_dict["ppump"])

# log action
LF.logFunc(logloc=logloc, line="flipRelayWH changed status. North: " + LF.l2s(WHN_status) + ", South: " + LF.l2s(WHN_status))
