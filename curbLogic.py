#!/usr/bin/python3

import local_functions as LF
import os
import sys
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
initial_dict = LF.gpioCheckStatus(["WH_north", "WH_south"])
WHN_status = [initial_dict["WH_north"]] # start list that will be [before, after]
WHS_status = [initial_dict["WH_south"]] # start list that will be [before, after]

# for production-based override
isSchoolHours = int(strftime("%H",localtime())) in range(6,14)
isWeekday = int(strftime("%w",localtime())) in range(1,6)
month = int(strftime("%m", localtime()))
PRD = LF.averageProduction(jsonloc)
lowProduction = (month in range(3,11) and PRD < 5000) or (month in [1,2,11,12] and PRD < 4000)

# status_message starts with lag indicator if there's a lag
# status_message = "Curb: " + strftime("%H:%M:%S", localtime(first_json_timestamp)) + ", "
# if data_lag > 240:
#	status_message += "(Data lag " + str(data_lag) + "s) "
status_message = ""

# Decide whether and what to override
if LF.isOn("HPS", HPS) or LF.isOn("HPN", HPN): # if either heat pump is on, turn both water heaters off
	status_message += "Heat pump(s) on (" + str(HPN) + "w and " + str(HPS) + "w), turning off both water heaters."
	LF.gpioSetStatus(status_dict = {"WH_north": 0, "WH_south": 0})

elif LF.isOn("DRY", DRY): # if dryer is on, turn both water heaters off
	status_message += "Dryer running (" + str(DRY) + " w), turning off both water heaters."
	LF.gpioSetStatus(status_dict = {"WH_north": 0, "WH_south": 0})

elif LF.isOn("SUB", SUB): # if kitchen consumption is really high, turn both water heaters off
	status_message += "Kitchen consumption very high (" + str(SUB) + " w), turning off both water heaters."
	LF.gpioSetStatus(status_dict = {"WH_north": 0, "WH_south": 0})

# don't let water heaters run during school hours on weekdays if production is low
elif isWeekday and isSchoolHours and lowProduction:
	status_message += "Low production (" + str(PRD) + " w), turning off both water heaters."
	LF.gpioSetStatus(status_dict = {"WH_north": 0, "WH_south": 0})

# if one water heater is on, turn the other off -- prioritize north because more showers are there
elif LF.isOn("WHN", WHN):
	status_message += "North water heater on (" + str(WHN) + " w), turning off south water heater."
	LF.gpioSetStatus(status_dict = {"WH_north": 1, "WH_south": 0})

elif LF.isOn("WHS", WHS):
	status_message += "South water heater on (" + str(WHS) + " w), turning off north water heater."
	LF.gpioSetStatus(status_dict = {"WH_north": 0, "WH_south": 1})

# if north is allowed but not running, then that happened last run of this program. Turn both on. North didn't need to run.
elif LF.gpioCheckStatus("WH_north")["WH_north"] == 1 and not LF.isOn("WHN", WHN):
	status_message += "No devices running, allowing both water heaters to run."
	LF.gpioSetStatus(status_dict = {"WH_north": 1, "WH_south": 1})

else:
	status_message += "No devices running, allowing north water heater to run."
	LF.gpioSetStatus(status_dict = {"WH_north": 1, "WH_south": 0})

end_dict = LF.gpioCheckStatus(["WH_north", "WH_south"])
WHN_status.append(end_dict["WH_north"])
WHS_status.append(end_dict["WH_south"])

# If status of either WH changed, note it.
any_change = 0
for status in [WHN_status, WHS_status]:
	change = int(status[1] != status[0])
	any_change += change

if any_change:
	status_add = " WHN:" + l2s(WHN_status) + " WHS:" + l2s(WHS_status)
	status_message += status_add
	LF.logFunc(logloc=logloc, line=status_message)

#elif (WHN_status, WHS_status) != ([1, 1], [1, 1]):
#	tmp = {"HPN": HPN, "HPS": HPS, "WHN": WHN, "WHS": WHS, "DRY": DRY, "SUB": SUB, "PP": PP, "status N,S": (WHN_status, WHS_status)}
#	LF.logFunc(logloc=logloc, line="No changes. " + dumps(tmp))
