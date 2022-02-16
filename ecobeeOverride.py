#!/usr/bin/python3

import os
import sys
import time
import local_functions as LF
from subprocess import call
from json import loads

# env variables
CurbLocationID = os.environ["CURB_LOCATION_ID"]
CurbAPIurl = os.environ["CURB_API_URL"]
CurbAT = os.environ["CURB_ACCESS_TOKEN"]
RT = os.environ['ECOBEE_REFRESH_TOKEN']
logloc = os.environ['CURB_LOCAL_LOG_LOC']
jsonloc = os.environ['CURB_LOCAL_JSON_LOC']


def logShortcut (msg, hs): # just needed for verbose logging while working out kinks, bugs, etc.
	hs2 = "HPN " + hs
	myStr = "Curb = " + consTime + ", " + hs2 + ", liveHoldFlag = " + str(liveHoldFlag) + ", messageFlag = " + str(messageFlag) + \
			", HPN = " + str(HPN) + ", HPS = " + str(HPS) + ", " + msg
	return myStr


# log program launch
LF.logFunc(logloc=logloc, line="ecobeeOverride launched")

# list of high consumption circuits for use in loop
hogs = ["Water Heater South", "Water Heater North", "Pool Pump 1", "Pool Pump 2", \
		"Dryer 1", "Dryer 2", "Heat Pump North", "Sub Panel 1", "Sub Panel 2"]

# Initialize variables
liveHoldFlag = False
messageFlag = False
jsonErrors = 0

while True:

	# get consumption data from latest line in consumption_log.json
	try:
		usage = LF.readConsumptionJSON(jsonloc = jsonloc)
		consTime = time.strftime("%H:%M:%S", time.localtime(usage["timestamp"]))
		WHS, WHN, DRY, HPS, HPN, SUB, PP, totalHogConsumption = LF.curbUsage(usage)
		jsonErrors = max(0, jsonErrors - 1)
	except BaseException:
		jsonErrors += 1
		LF.logFunc(logloc = logloc, line = "ERROR: Problems reading/parsing consumption JSON file. Trying to continue.")
		if jsonErrors > 2:
			sys.exit("Too many errors in a row reading/parsing consumption JSON file. I give up.")

	# if certain conditions, set an override hold on the ecobee for holdInterval (default=4) minutes
	# conditions: HPN is on, Kitchen usage is very high, total hog consumption is > 8000, or dryer is on
	if LF.isOn("HPN", HPN) or LF.isOn("SUB", SUB) or totalHogConsumption > 8000 or LF.isOn("DRY", DRY):

		# Why do we fire?
		hpn_on = int(LF.isOn("HPN", HPN) == 1)
		sub_on = int(LF.isOn("SUB", SUB) == 1)
		dry_on = int(LF.isOn("DRY", DRY) == 1)
		hog_on = int(totalHogConsumption > 8000)
		reason = sum([1000 * hpn_on, 100 * sub_on, 10 * dry_on, hog_on])

		hs = "ON"
		if liveHoldFlag == False:

			# update ecobee access token
			try:
				jkey = LF.refreshEcobeeAuthToken(refresh_token=RT)
				ECOBEE_TOKEN, ECOBEE_TOKEN_TYPE, ECOBEE_REFRESH_TOKEN, ECOBEE_TOKEN_EXPIRY, ECOBEE_SCOPE2 = jkey.values()
#				LF.logFunc(logloc=logloc, line=logShortcut(msg = "ran refreshEcobeeAuthToken (1)", hs = hs))
			except Exception:
				LF.handleException(msg="Problem refreshing Ecobee token (1) using refresh token in ecobeeOverride.py", logloc=logloc)

			# query thermostats to get necessary data fields
			try:
				temps, thermostatTime = LF.queryEcobee(auth_token=ECOBEE_TOKEN)
#				LF.logFunc(logloc=logloc, line=logShortcut(msg = "ran queryEcobee()", hs = hs))
			except Exception:
				LF.handleException(msg="Problem querying ecobee to get temps and time", logloc=logloc)

			# Run postHold function
			try:
				setHold, endEpoch, resultAPI = LF.postHold(auth_token=ECOBEE_TOKEN, thermostatTime=thermostatTime, heatRangeLow=temps[0], coolRangeHigh=temps[1])
#				LF.logFunc(logloc=logloc, line=logShortcut(msg = "ran postHold()", hs = hs))
				if resultAPI[3] != 200:
				  LF.logFunc(logloc=logloc, line=logShortcut(msg=resultAPI[0] + " received a non-200 response from setHold (" + str(resultAPI[3]) + ")", hs = hs))
			except Exception:
				LF.handleException(msg="Problem with postHold in ecobeeOverride.py", logloc=logloc)

			# log the override (if this is the first time xough the loop with HPN on)
			if messageFlag == False:
				LF.logFunc(logloc = logloc, line = "Setting an override hold on south heat pump (reason " + f'{reason:04d}' + ")")
				messageFlag = True

			# set live hold flag to indicate active hold
			liveHoldFlag = True

		else: # if HPN is on and liveHoldFlag is already True, there's no new news. Wait 60 or until expiry
			remainingHold = endEpoch - time.mktime(time.localtime())
			if remainingHold < 60:
#				LF.logFunc(logloc = logloc, line = logShortcut(msg="sleeping " + str(remainingHold), hs = hs) + ", remainingHold = " + str(remainingHold))
				time.sleep(max(remainingHold - 3, 1))
				liveHoldFlag = False
			else:
#				LF.logFunc(logloc = logloc, line = logShortcut(msg = "sleeping 60", hs = hs) + ", remainingHold = " + str(remainingHold))
				time.sleep(60)

	else: # if HPN is not on (<= 300)
		hs = "OFF"
		if liveHoldFlag == True: # if HPN is off but live hold flag is set, we are first detecting that HPN has ended. Resume program, set live hold flag to false.

			# update ecobee access token
			try:
				jkey = LF.refreshEcobeeAuthToken(refresh_token=RT)
				ECOBEE_TOKEN, ECOBEE_TOKEN_TYPE, ECOBEE_REFRESH_TOKEN, ECOBEE_TOKEN_EXPIRY, ECOBEE_SCOPE2 = jkey.values()
#				LF.logFunc(logloc=logloc, line=logShortcut(msg = "ran refreshEcobeeAuthToken (2)", hs = hs))
			except Exception:
				LF.handleException(msg="Problem refreshing Ecobee token (2) using refresh token", logloc=logloc)

			# resume program (cancel hold)
			try:
				rP, resultAPI = LF.resumeProgram(auth_token=ECOBEE_TOKEN)
#				LF.logFunc(logloc = logloc, line = logShortcut(msg = "ran resumeProgram()", hs = hs))
				if resultAPI[3] != 200:
				  LF.logFunc(logloc=logloc, line = logShortcut(msg=resultAPI[0] + " received a non-200 response from resumeProgram (" + str(resultAPI[3]) + ")", hs = hs))
			except Exception:
				LF.handleException(msg="Problem cancelling hold in ecobeeOverride.py", logloc=logloc)

			# log the resumption (since is the first loop detecting cessation of HPN activity)
			LF.logFunc(logloc=logloc, line="North heat pump no longer running, allowing south heat pump (ecobee) to resume program")

			liveHoldFlag = False # set live hold flag to indicate no active hold
			messageFlag = False # set messageFlag to false so log message is written next time HPN kicks on

		else: # if HPN is off and no hold is currently active, there's no new news. Wait 60.
			time.sleep(60)
