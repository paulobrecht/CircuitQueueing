#!/usr/bin/python3

import time
import json
import RPi.GPIO as gpio
import os
import sys
from local_functions import logfunc
from local_functions import curbQuery

# mapping 0/1 to OFF/ON
map = {0:"OFF", 1:"ON"}

# Water heater GPIO setup
WH_north, WH_south, ppump = [11, 13, 15] # board pins
gpio.setmode(gpio.BOARD)
gpio.setwarnings(False)
gpio.setup(WH_north,gpio.OUT)
gpio.setup(WH_south,gpio.OUT)
gpio.setup(ppump,gpio.OUT)

# Check/store initial status of each as first item of what will be a two-item list
WHN_status = [gpio.input(WH_north)]
WHS_status = [gpio.input(WH_south)]
PP_status  = [gpio.input(ppump)]

# Call query function and parse returned values
now = time.strftime("%H:%M:%S", time.localtime())
locationID=os.environ["CURB_LOCATION_ID"]
apiURL=os.environ["CURB_API_URL"]
AT = os.environ["CURB_ACCESS_TOKEN"]
logloc = os.environ['CURB_LOCAL_LOG_LOC']

usage, latest_json = curbQuery(locationID=locationID, apiURL=apiURL, AT=AT)

if usage == "ERROR":
  logfunc(logloc=logloc, line=str("ERROR: Issues with Curb query (1): " + str(latest_json)))
  sys.exit()
else:
  WHS, WHN, DRY, HPS, HPN, SUB, PP = usage

# Logic

# Thresholds
T_HP = 300
T_DRY = 100
T_SUB1 = 3000
T_SUB2 = 1000
T_WH = 500

if HPN > T_HP or HPS > T_HP: # if either heat pump is on, turn both water heaters and pool pump off
  Status_message = "Heat pump(s) on (" + str(HPN) + "w and " + str(HPS) + "w), turning off both water heaters and pool pump."
  gpio.output(WH_north,0)
  gpio.output(WH_south,0)
  gpio.output(ppump,0)
elif DRY > T_DRY: # if dryer is on, turn both water heaters and pool pump off
  Status_message = "Dryer running (" + str(DRY) + " w), turning off both water heaters and pool pump."
  gpio.output(WH_north,0)
  gpio.output(WH_south,0)
  gpio.output(ppump,0)
elif SUB > T_SUB1: # if kitchen consumption is really high, turn both water heaters and pool pump off
  Status_message = "Kitchen consumption very high (" + str(SUB) + " w), turning off both water heaters and pool pump."
  gpio.output(WH_north,0)
  gpio.output(WH_south,0)
  gpio.output(ppump,0)
elif SUB > T_SUB2: # if kitchen consumption is only kinda high, turn just water heaters off, don't force pool pump either way
  Status_message = "Kitchen consumption high (" + str(SUB) + " w), turning off both water heaters."
  gpio.output(WH_north,0)
  gpio.output(WH_south,0)
elif WHN > T_WH: # if one water heater is on, turn the other and pool pump off -- prioritize north because more showers are there
  Status_message = "North water heater on (" + str(WHN) + " w), turning off south water heater and pool pump."
  gpio.output(WH_south,0)
  gpio.output(ppump,0)
elif WHS > T_WH:
  Status_message = "South water heater on (" + str(WHS) + " w), turning off north water heater and pool pump."
  gpio.output(WH_north,0)
  gpio.output(ppump,0)
else:

  # no large consumers are running, allow water heaters and pool pump to run
  # BUT turn on water heaters and wait 30 seconds. Then if neither water heater kicks on, THEN allow pool pump to run

  if WHN_status[0] == 1 and WHS_status[0] == 1 and PP_status[0] == 1: # if nothing was overridden before, and nothing is overridden now.
    gpio.output(WH_north,1)
    gpio.output(WH_south,1)
    gpio.output(ppump,1)
  else: # if something was overriden before, but now nothing is, then turn on water heaters and check again in 30 s
    Status_message = "No other devices running, allowing both water heaters"
    gpio.output(WH_north,1)
    gpio.output(WH_south,1)
    gpio.output(ppump,0)

    time.sleep(30)
    usage2, latest_json2 = curbQuery(locationID=locationID, apiURL=apiURL, AT=AT)

    if usage2 == "ERROR":
      logfunc(logloc=logloc, line=str("ERROR: Issues with Curb query (2): " + str(latest_json2)))
      sys.exit()
    else:
      if usage2[0] > T_WH or usage2[1] > T_WH:
        gpio.output(ppump,0)
        Status_message = Status_message + " (" + str(usage2[0]) + ", " + str(usage2[1]) + ") to run."
      else:
        gpio.output(ppump,1)
        Status_message = Status_message + " (" + str(usage2[0]) + ", " + str(usage2[1]) + ") and pool pump (" + str(usage2[6]) + ") to run."

# Check/store status after making changes
WHN_status.append(gpio.input(WH_north))
WHS_status.append(gpio.input(WH_south))
PP_status.append(gpio.input(ppump))

# If status of either WH or pool pump changed, note it.
WHN_change = (WHN_status[0] !=  WHN_status[1])
WHS_change = (WHS_status[0] !=  WHS_status[1])
PP_change = (PP_status[0] !=  PP_status[1])

if WHN_change or WHS_change or PP_change:
  tmp_change1 = Status_message
  tmp_change2 = str(" WHN:" + map[WHN_status[0]] + "->" + map[WHN_status[1]] + ", ")
  tmp_change3 = str(" WHS:" + map[WHS_status[0]] + "->" + map[WHS_status[1]] + ", ")
  tmp_change4 = str(" PP:"  + map[PP_status[0]]  + "->" + map[PP_status[1]])
  logfunc(logloc=logloc, line=str(tmp_change1 + tmp_change2 + tmp_change3 + tmp_change4))
else:
  tmp = {"HPN": HPN, "HPS": HPS, "PP": PP, "DRY": DRY, "SUB": SUB, "WHN": WHN, "WHS": WHS, "WHN_stat": WHN_status, "WHS_stat": WHS_status, "PP_stat": PP_status}
  logfunc(logloc=logloc, line=str(json.dumps(tmp)))


# Now, write all activity to a separate file

# outer dict
stuff_keys = ["timestamp", "consumption", "production", "net"]
stuff = {key: latest_json[key] for key in stuff_keys}

circuits2 = {}
for key in stuff_keys:
   circuits2[key] = stuff[key]

# inner dict
circuits = latest_json["circuits"]

i=1
for item in circuits:
  try:
    newk = item["id"]
  except KeyError:
    label = "Orphan " + str(i)
    circuits2[label] = item["w"]
    i += 1
  else:
    circuits2[item["label"]] = item["w"]

# json file
jsonloc = os.environ['CURB_LOCAL_JSON_LOC']
for_output=json.dumps(circuits2)
logfunc(now="", logloc=jsonloc, line=for_output)
