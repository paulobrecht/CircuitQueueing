#!/usr/bin/python3

import local_functions as LF
import os
import sys
from time import sleep, localtime, strftime, mktime
from json import dumps

sleep(10) # to give fetchCurbData.py a chance to write before this program tries to read its output

# convience func to change [0, 1] to "OFF->ON"
def l2s(se):
	initial = LF.gpioMaps()[1][se[0]]
	end = LF.gpioMaps()[1][se[1]]
	return str(initial) + "->" + str(end)

# convience func to read JSON file and compare timestamps
def readit():
	usage = LF.readConsumptionJSON(jsonloc)
	data_lag = usage['data_lag']
	curb_timestamp = usage["timestamp"]
	return([usage, data_lag, curb_timestamp])

logloc = os.environ['CURB_LOCAL_LOG_LOC']
jsonloc = os.environ['CURB_LOCAL_JSON_LOC']

# counter for retry up ahead
i=0

# read latest row in json file
try:
	trying = readit()
	data_lag = trying[1]
except BaseException:
	LF.logFunc(logloc = logloc, line = "ERROR: Problems reading/parsing consumption JSON file." + jsonloc)
	sys.exit()

# if data lag is > 2 minutes, wait a bit for the next update
# but not too long, or this run might interfere with the next run
try:
	if data_lag > 120:
		first_curb_timestamp = trying[2]
		while i < 10:
			sleep(5)
			trying = readit()
			if trying[2] > first_curb_timestamp:
				break
			else:
				i += 1

	# either right away, or after trying a few times, parse the jsonfile
	WHS, WHN, DRY, HPS, HPN, SUB, PP, totalHogConsumption = LF.curbUsage(trying[0])

	# log for testing how well this works and how often it's triggered
	# log = open("/home/pi/CurbAPI/testlag.txt", "a")
	# now = strftime("%H:%M:%S", localtime())
	# log.write(now + ": " + "latest timestamp = " + str(trying[2]) + ", i = " + str(i) + ", orig_data_lag = " + str(data_lag) + "\n")
except BaseException:
	LF.logFunc(logloc = logloc, line = "ERROR: Problems in readConsumptionJSON() retry loop. Exiting.")
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
PRD = abs(LF.averageProduction(jsonloc))
lowProduction = (month in range(3,11) and PRD < 5000) or (month in [1,2,11,12] and PRD < 4000)

# status_message starts with lag indicator if there's a lag
# status_message = "Curb: " + strftime("%H:%M:%S", localtime(first_json_timestamp)) + ", "
# if data_lag > 240:
#	status_message += "(Data lag " + str(data_lag) + "s) "
status_message = ""

# Decide whether and what to override
if LF.isOn("HPN", HPN): # if either heat pump is on, turn both water heaters off
	status_message += "North heat pump on (" + str(HPN) + "w), water heater override."
	LF.gpioSetStatus(status_dict = {"WH_north": 0, "WH_south": 0})

elif LF.isOn("HPS", HPS): # if either heat pump is on, turn both water heaters off
	status_message += "South heat pump on (" + str(HPS) + "w), water heater override."
	LF.gpioSetStatus(status_dict = {"WH_north": 0, "WH_south": 0})

elif LF.isOn("DRY", DRY): # if dryer is on, turn both water heaters off
	status_message += "Dryer running (" + str(DRY) + " w), water heater override."
	LF.gpioSetStatus(status_dict = {"WH_north": 0, "WH_south": 0})

elif LF.isOn("SUB", SUB): # if kitchen consumption is really high, turn both water heaters off
	status_message += "Kitchen consumption very high (" + str(SUB) + " w), water heater override."
	LF.gpioSetStatus(status_dict = {"WH_north": 0, "WH_south": 0})

# don't let water heaters run during school hours on weekdays if production is low
elif isWeekday and isSchoolHours and lowProduction:
	status_message += "Low production (" + str(PRD) + " w), water heater override."
	LF.gpioSetStatus(status_dict = {"WH_north": 0, "WH_south": 0})

# if one water heater is on, turn the other off -- prioritize north because more showers are there
elif LF.isOn("WHN", WHN):
	status_message += "North water heater on (" + str(WHN) + " w), south water heater override."
	LF.gpioSetStatus(status_dict = {"WH_north": 1, "WH_south": 0})

elif LF.isOn("WHS", WHS):
	status_message += "South water heater on (" + str(WHS) + " w), north water heater override."
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
