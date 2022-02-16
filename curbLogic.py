#!/usr/bin/python3

import local_functions as LF
import os
from time import sleep, localtime, strftime, mktime
from json import dumps

# convience func to change [0, 1] to "OFF->ON"
def l2s(se):
	initial = LF.gpioMaps()[1][se[0]]
	end = LF.gpioMaps()[1][se[1]]
	return str(initial) + "->" + str(end)

logloc = os.environ['CURB_LOCAL_LOG_LOC']
jsonloc = os.environ['CURB_LOCAL_JSON_LOC']

try:
	usage = LF.readConsumptionJSON(jsonloc)
	first_json_timestamp = usage["timestamp"]
	data_lag = int(round(mktime(localtime()) - usage["timestamp"]))
	WHS, WHN, DRY, HPS, HPN, SUB, PP, totalHogConsumption = LF.curbUsage(usage)
except BaseException:
	LF.logFunc(logloc = logloc, line = "ERROR: Problems reading/parsing consumption JSON file.")
	sys.exit()

############
# Curb Logic
############

# initial values
initial_dict = LF.gpioCheckStatus(["WH_north", "WH_south", "ppump"])
WHN_status = [initial_dict["WH_north"]] # start list that will be [before, after]
WHS_status = [initial_dict["WH_south"]] # start list that will be [before, after]
PP_status  = [initial_dict["ppump"]] # start list that will be [before, after]

# status_message starts with lag indicator if there's a lag
status_message = "Curb: " + strftime("%H:%M:%S", localtime(first_json_timestamp)) + ", "
if data_lag > 240:
	status_message += "(Data lag " + str(data_lag) + "s) "

# Decide whether and what to override
if LF.isOn("HPS", HPS) or LF.isOn("HPN", HPN): # if either heat pump is on, turn both water heaters and pool pump off
	status_message += "Heat pump(s) on (" + str(HPN) + "w and " + str(HPS) + "w), turning off both water heaters and pool pump."
	LF.gpioSetStatus(status_dict = {"WH_north": 0, "WH_south": 0, "ppump": 0})

elif LF.isOn("DRY", DRY): # if dryer is on, turn both water heaters and pool pump off
	status_message += "Dryer running (" + str(DRY) + " w), turning off both water heaters and pool pump."
	LF.gpioSetStatus(status_dict = {"WH_north": 0, "WH_south": 0, "ppump": 0})

elif LF.isOn("SUB", SUB): # if kitchen consumption is really high, turn both water heaters and pool pump off
	status_message += "Kitchen consumption very high (" + str(SUB) + " w), turning off both water heaters and pool pump."
	LF.gpioSetStatus(status_dict = {"WH_north": 0, "WH_south": 0, "ppump": 0})

# if one water heater is on, turn the other and pool pump off -- prioritize north because more showers are there
elif LF.isOn("WHN", WHN):
	status_message += "North water heater on (" + str(WHN) + " w), turning off south water heater and pool pump."
	LF.gpioSetStatus(status_dict = {"WH_north": 1, "WH_south": 0, "ppump": 0})

elif LF.isOn("WHS", WHS):
	status_message += "South water heater on (" + str(WHS) + " w), turning off north water heater and pool pump."
	LF.gpioSetStatus(status_dict = {"WH_north": 0, "WH_south": 1, "ppump": 0})

else:
	status_message += "No other devices running, allowing water heaters and pool pump (" + \
	                   str(WHN) + " w, " + str(WHS) + " w, " + str(PP) + " w) to run."
	LF.gpioSetStatus(status_dict = {"WH_north": 1, "WH_south": 1, "ppump": 1})

end_dict = LF.gpioCheckStatus(["WH_north", "WH_south", "ppump"])
WHN_status.append(end_dict["WH_north"])
WHS_status.append(end_dict["WH_south"])
PP_status.append(end_dict["ppump"])

# If status of either WH or pool pump changed, note it.
any_change = 0
for status in [WHN_status, WHS_status, PP_status]:
	change = int(status[1] != status[0])
	any_change += change

if any_change:
	status_add = " WHN:" + l2s(WHN_status) + " WHS:" + l2s(WHS_status) + " PP:" + l2s(PP_status)
	status_message += status_add
	LF.logFunc(logloc=logloc, line=status_message)
elif (WHN_status, WHS_status, PP_status) != ([1, 1], [1, 1], [1, 1]):
	tmp = {"HPN": HPN, "HPS": HPS, "WHN": WHN, "WHS": WHS, "DRY": DRY, "SUB": SUB, "PP": PP, "status N,S,PP": (WHN_status, WHS_status, PP_status)}
	LF.logFunc(logloc=logloc, line="No changes. " + dumps(tmp))
