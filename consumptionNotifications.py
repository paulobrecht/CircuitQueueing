#!/usr/bin/python3

import local_functions as LF
import os
import sys
from time import sleep, localtime, strftime, mktime
from json import dumps

logloc = os.environ['CURB_LOCAL_LOG_LOC']
jsonloc = os.environ['CURB_LOCAL_JSON_LOC']

try:
	usage = LF.readConsumptionJSON(jsonloc)
except BaseException:
	LF.logFunc(logloc = logloc, line = "ERROR: consumptionNotifications could not read/parse consumption JSON file.")
	sys.exit()

cons_keys = ['Heat Pump North', 'Heat Pump South', 'Water Heater North', 'Water Heater South', 'Pool Pump 1', 'Pool Pump 2', \
             'Sub Panel 1', 'Sub Panel 2', 'Dryer 1', 'Dryer 2', 'Small Garage', 'Office outlets', 'Living room', \
             'Master & 3rd Bedroom', '2 W Bedrooms & Hall Bathroom', "consumption", "production", "timestamp"]

cons = {key: usage[key] for key in cons_keys}
HPN, HPS, WHN, WHS, PP1, PP2, SUB1, SUB2, DRY1, DRY2, GRG_SM, OFC, LVG, MST_3RD, W2_HB, CONS, PROD, TIME = cons.values()
consTime = strftime("%H:%M:%S", localtime(TIME))
SUB = SUB1 + SUB2
DRY = DRY1 + DRY2
PP = PP1 + PP2

# use timestamp from JSON for this instead of actual time. If there are Curb query errors,
# there will be missing rows in the JSON file, and isPPtime errors will fire when it is not
# actually in fact PP time.
nowHour = int(strftime("%H",localtime(TIME)))
isPPtime = nowHour in [10,12,13,14] # omit 11 because pool pump is off from 11-12 to allow water heaters to run

def notice(msg):
	string = consTime + ": " + msg
	return string

############
# Checks
############

##########################################
# Check if production is not 0 for a long time. At night, it tends to be 14 or -22. It was 0 when breaker to solar was off.
##########################################
avgProd = abs(LF.averageProduction(jsonloc=jsonloc, duration=15))
if avgProd == 0:
	msg = notice("Average production in the past 15 minutes is exactly 0 W. Is the solar sytem on?")
	LF.prowl(msg=msg, short="Production is zero.")

# small garage consumption > 200 likely means light is on
if GRG_SM > 200:
	msg = notice("Small garage consumption is " + str(GRG_SM) + " W.")
	LF.prowl(msg=msg, short="Small garage consumption high.")

# consumption is very high
if CONS > 12000:
	msg = notice("Overall electricity consumption is " + str(CONS) + " W.")
	LF.prowl(msg=msg, short="Overall consumption high.")

# Pool pump should be running but it's not
if isPPtime == True and PP < 100:
	msg = notice("Pool pump should be on between 10 am and 3 pm, but it's not on.")
	LF.prowl(msg=msg, short="Pool pump off.")

# Dryer is on
startTime, minutesOn = LF.firstOnDryerTime(jsonloc)
if startTime != False: # func returns false if device is not on now
  if minutesOn > 75:
    msg = notice("Dryer has been on since " + startTime + ".")
    LF.prowl(msg=msg, short="Dryer on for " + str(minutesOn) + " minutes.")

# if LF.isOn("DRY", DRY):
# 	msg = notice("Dryer is consuming " + str(DRY) + " W.")
# 	LF.prowl(msg=msg, short="Dryer on.")

# Master/3rd bedroom use is high
if MST_3RD > 600:
	msg = notice("Master/3rd bedroom consumption is " + str(MST_3RD) + " W.")
	LF.prowl(msg=msg, short="MBR/3rd consumption high.")

# 2 West bedrooms/hall bathroom use is high
if W2_HB > 500:
	msg = notice("Two west bedrooms/hall bathroom consumption is " + str(W2_HB) + " W.")
	LF.prowl(msg=msg, short="2 west BR consumption high.")
