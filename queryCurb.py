#!/usr/bin/python3

import time
import json
import RPi.GPIO as gpio
import os
from sys import exit
from local_functions import logfunc
from local_functions import curbQuery

# don't run at 5 am, 9 am, or 9 pm when WHs comes back on. Wait one minute for logic in flipRelayWH.py to execute.
dt = time.strftime("%H:%M", time.localtime())
if dt in ["05:00", "09:00", "21:00"]:
  sys.exit()

# mapping 0/1 to OFF/ON
map = {0:"OFF", 1:"ON"}

# Water heater GPIO setup
WH_north, WH_south, ppump = [11, 13, 15] # board pins
gpio.setmode(gpio.BOARD)
gpio.setwarnings(False)
gpio.setup(WH_north,gpio.OUT)
gpio.setup(WH_south,gpio.OUT)
gpio.setup(ppump,gpio.OUT)

# Check/store status before logic
WHN_status = [gpio.input(WH_north)]
WHS_status = [gpio.input(WH_south)]
PP_status  = [gpio.input(ppump)]

# Call query function and parse returned values
now = time.strftime("%H:%M:%S", time.localtime())
locationID=os.environ["CURB_LOCATION_ID"]
apiURL=os.environ["CURB_API_URL"]
AT = os.environ["CURB_ACCESS_TOKEN"]
logloc = os.environ['CURB_LOCAL_LOG_LOC']

[usage, latest_json] = curbQuery(locationID=locationID, apiURL=apiURL, AT=AT)

if usage == "ERROR":
  logfunc(time=now, logloc=logloc, line=str("ERROR: Issues with Curb query: " + str(latest_json)))
  raise SystemExit("ERROR: Query error.")
else:
  WHS, WHN, DRY, HPS, HPN, SUB, PP = usage

# Logic
if HPN > 300 or HPS > 300: # if either heat pump is on, turn both water heaters and pool pump off
  Status_message = "Heat pump(s) on (" + str(HPN) + "w and " + str(HPS) + "w), turning off both water heaters and pool pump."
  gpio.output(WH_north,0)
  gpio.output(WH_south,0)
  gpio.output(ppump,0)
elif DRY > 100: # if dryer is on, turn both water heaters and pool pump off
  Status_message = "Dryer running (" + str(DRY) + " w), turning off both water heaters and pool pump."
  gpio.output(WH_north,0)
  gpio.output(WH_south,0)
  gpio.output(ppump,0)
elif SUB > 3000: # if kitchen consumption is really high, turn both water heaters and pool pump off
  Status_message = "Kitchen consumption very high (" + str(SUB) + " w), turning off both water heaters and pool pump."
  gpio.output(WH_north,0)
  gpio.output(WH_south,0)
  gpio.output(ppump,0)
elif SUB > 1000: # if kitchen consumption is only kinda high, turn just water heaters off (but explicitly allow pool pump to run)
  Status_message = "Kitchen consumption high (" + str(SUB) + " w), turning off both water heaters."
  gpio.output(WH_north,0)
  gpio.output(WH_south,0)
  gpio.output(ppump,1)
elif WHN > 1000: # if one water heater is on, turn the other and pool pump off
  Status_message = "North water heater on (" + str(WHN) + " w), turning off south water heater and pool pump."
  gpio.output(WH_south,0)
  gpio.output(ppump,0)
elif WHS > 1000:
  Status_message = "South water heater on (" + str(WHS) + " w), turning off north water heater and pool pump."
  gpio.output(WH_north,0)
  gpio.output(ppump,0)
else: # if none of these conditions holds, turn both water heaters and maybe pool pump on
  Status_message = "No other devices running, allowing both water heaters"
  gpio.output(WH_north,1)
  gpio.output(WH_south,1)
  # wait 30 sec to see if a water heater has turned on. If not, turn on pool pump too.
  # This prevents unnecessary competition and an additional pump startup/kill/startup cycle.
  time.sleep(15)

  usage = curbQuery(locationID=locationID, apiURL=apiURL, AT=AT)[0]

  if usage == "ERROR":
    logfunc(time=now, logloc=logloc, line=str("ERROR: Issues with Curb query: " + str(latest_json)))
    raise SystemExit("ERROR: Query error.")
  else:
    if usage[0] > 500 or usage[1] > 500:
      gpio.output(ppump,0)
      Status_message = Status_message + " to run."
    else:
      gpio.output(ppump,1)
      Status_message = Status_message + " and pool pump to run."

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
  logfunc(time=now, logloc=logloc, line=str(tmp_change1 + tmp_change2 + tmp_change3 + tmp_change4))
else:
  tmp = {"HPN": HPN, "HPS": HPS, "PP": PP, "DRY": DRY, "SUB": SUB, "WHN": WHN, "WHS": WHS, "WHN_stat": WHN_status, "WHS_stat": WHS_status, "PP_stat": PP_status}
  logfunc(time=now, logloc=logloc, line=str(json.dumps(tmp)))


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
logfunc(logloc=jsonloc, line=for_output)
