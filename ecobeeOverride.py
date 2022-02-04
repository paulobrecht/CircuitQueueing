#!/usr/bin/python3

import os
import time
import sys
from subprocess import call
import local_functions
import ecobee_functions

# env variables
CurbLocationID = os.environ["CURB_LOCATION_ID"]
CurbAPIurl = os.environ["CURB_API_URL"]
CurbAT = os.environ["CURB_ACCESS_TOKEN"]
logloc = os.environ['CURB_LOCAL_LOG_LOC']
RT = os.environ['ECOBEE_REFRESH_TOKEN']

# it's impossible to kick this script off after midnight without a correcive argument
if len(sys.argv) > 1:
  if sys.argv[1] == "Yesterday":
    tmp = time.mktime(time.localtime()) - 86400 # 24 hours ago
    launchTime = time.localtime(tmp)
  else:
    raise Exception("Program argument must be 'Yesterday' or nothing at all.")
else:
  launchTime = time.localtime()

# log program launch
local_functions.logfunc(logloc=logloc, line="ecobeeOverride launched")

# time calculations
launchDay = time.strftime("%Y-%m-%d", launchTime)
launchDayMidnight = time.strptime(launchDay + " 00:00:00", "%Y-%m-%d %H:%M:%S")

# this program runs once a day starting at 4:30 am
# So loop until 4:30 and then exit

try:
  now = time.localtime()
  nowDay = time.strftime("%Y-%m-%d", now)
  minsSinceLaunchDayMidnight = (time.mktime(now) - time.mktime(launchDayMidnight)) / 60

  liveHoldFlag = False
  messageFlag = False
  cont = (nowDay == launchDay and 270 <= minsSinceLaunchDayMidnight < 1440) or (nowDay != launchDay and 1440 <= minsSinceLaunchDayMidnight < 1710)

  while cont:

    # query curb for HPN (north heat pump) electricity consumption
    try:
      usage = local_functions.curbQuery(locationID=CurbLocationID, apiURL=CurbAPIurl, AT=CurbAT)[0]
    except Exception:
      local_functions.logfunc(logloc=logloc, line="ERROR: Problem with curbQuery() in ecobeeOverride.py. Exiting.")
      execStr = "./prowl.sh " + "ERROR: ecobeeOverride.py has exited abnormally."
      rc = call(execStr)
      raise Exception("ERROR: Problem with curbQuery() in ecobeeOverride.py. Exiting.")
    HPN = usage[4]
    HPS = usage[3]

    # if HPN is on and no hold is currently active, set an override hold on the ecobee for holdInterval (default=4) minutes
    if HPN > 300:

      if liveHoldFlag == False:

        # update ecobee access token
        try:
          jkey = ecobee_functions.refreshEcobeeAuthToken(refresh_token=RT)
          ECOBEE_TOKEN, ECOBEE_TOKEN_TYPE, ECOBEE_REFRESH_TOKEN, ECOBEE_TOKEN_EXPIRY, ECOBEE_SCOPE2 = jkey.values()
          print(str(time.asctime()) + ": HPN > 300" + ", ran refreshEcobeeAuthToken(), HPN = " + str(HPN) + ", HPS = " + str(HPS) + ", liveHoldFlag = " + \
          str(liveHoldFlag) + ", messageFlag = " + str(messageFlag))
        except Exception:
          local_functions.logfunc(logloc=logloc, line="ERROR: Problem refreshing Ecobee token (1) using refresh token in ecobeeOverride.py. Exiting.")
          execStr = "./prowl.sh " + "ERROR: ecobeeOverride.py has exited abnormally."
          rc = call(execStr)
          raise Exception("ERROR: Problem refreshing Ecobee token (1) using refresh token in ecobeeOverride.py. Exiting.")

        # query thermostats to get necessary data fields
        try:
          temps, thermostatTime = ecobee_functions.queryEcobee(auth_token=ECOBEE_TOKEN)
          print(str(time.asctime()) + ": HPN > 300" + ", ran queryEcobee(), HPN = " + str(HPN) + ", HPS = " + str(HPS) + ", liveHoldFlag = " + str(liveHoldFlag) + \
          ", messageFlag = " + str(messageFlag))
        except Exception:
          local_functions.logfunc(logloc=logloc, line="ERROR: Problem querying ecobee to get temps and time in ecobeeOverride.py. Exiting.")
          execStr = "./prowl.sh " + "ERROR: ecobeeOverride.py has exited abnormally."
          rc = call(execStr)
          raise Exception("ERROR: Problem querying ecobee to get temps and time in ecobeeOverride.py. Exiting.")

        # Run setHold function
        try:
          setHold, endEpoch, resultAPI = ecobee_functions.postHold(auth_token=ECOBEE_TOKEN, thermostatTime=thermostatTime, heatRangeLow=temps[0], coolRangeHigh=temps[1])
          print(str(time.asctime()) + ": HPN > 300" + ", ran postHold(), HPN = " + str(HPN) + ", HPS = " + str(HPS) + ", liveHoldFlag = " + str(liveHoldFlag) + \
          ", messageFlag = " + str(messageFlag))
          if resultAPI[3] != 200:
            print(resultAPI[0] + " received a non-200 response (" + str(resultAPI[3]) + ")")
        except Exception:
          local_functions.logfunc(logloc=logloc, line="ERROR: Problem with setHold in ecobeeOverride.py. Exiting.")
          execStr = "./prowl.sh " + "ERROR: ecobeeOverride.py has exited abnormally."
          rc = call(execStr)
          raise Exception("ERROR: Problem with setHold in ecobeeOverride.py. Exiting.")

        # log the override (if this is the first time through the loop with HPN on)
        if messageFlag == False:
          local_functions.logfunc(logloc=logloc, line="North heat pump is running, setting an override hold on south heat pump")
          messageFlag = True

        # set live hold flag to indicate active hold
        liveHoldFlag = True

      else: # if HPN is on and liveHoldFlag is already True, there's no new news. Wait 30 or until expiry
        remainingHold = endEpoch - time.mktime(now)
        print(str(time.asctime()) + ": HPN > 300" + ", sleeping 30, HPN = " + str(HPN) + ", HPS = " + str(HPS) + ", liveHoldFlag = " + str(liveHoldFlag) + \
        ", messageFlag = " + str(messageFlag) + ", remainingHold = " + str(remainingHold))

        if remainingHold < 29:
          # there seems to be a lag of a couple of seconds in execution, keep letting one hold lapse for a few seconds before setting another, so subtract 5
          time.sleep(remainingHold)
        else:
          time.sleep(29)

    else: # if HPN is not on (<= 300)

      if liveHoldFlag == True: # if HPN is off but live hold flag is set, we are first detecting that HPN has ended. Resume program, set live hold flag to false.

        # update ecobee access token
        try:
          jkey = ecobee_functions.refreshEcobeeAuthToken(refresh_token=RT)
          ECOBEE_TOKEN, ECOBEE_TOKEN_TYPE, ECOBEE_REFRESH_TOKEN, ECOBEE_TOKEN_EXPIRY, ECOBEE_SCOPE2 = jkey.values()
        except Exception:
          local_functions.logfunc(logloc=logloc, line="ERROR: Problem refreshing Ecobee token (2) using refresh token in ecobeeOverride.py. Exiting.")
          execStr = "./prowl.sh " + "ERROR: ecobeeOverride.py has exited abnormally."
          rc = call(execStr)
          raise Exception("ERROR: Problem refreshing Ecobee token (2) using refresh token in ecobeeOverride.py. Exiting.")

        # resume program (cancel hold)
        try:
          rP = ecobee_functions.resumeProgram(auth_token=ECOBEE_TOKEN)
          print(str(time.asctime()) + ": HPN <= 300" + ", ran resumeProgram(), HPN = " + str(HPN) + ", HPS = " + str(HPS) + ", liveHoldFlag = " \
          + str(liveHoldFlag) + ", messageFlag = " + str(messageFlag))

        except Exception:
          local_functions.logfunc(logloc=logloc, line="ERROR: Problem cancelling hold in ecobeeOverride.py. Exiting.")
          execStr = "./prowl.sh " + "ERROR: ecobeeOverride.py has exited abnormally."
          rc = call(execStr)
          raise Exception("ERROR: Problem cancelling hold in ecobeeOverride.py. Exiting.")

        # log the resumption (since is the first loop detecting cessation of HPN activity)
        now = time.strftime("%H:%M:%S", time.localtime())
        local_functions.logfunc(logloc=logloc, line="North heat pump no longer running, allowing south heat pump (ecobee) to resume program")

        # set live hold flag to indicate no active hold
        liveHoldFlag = False

        # set messageFlag to false so log message is written next time HPN kicks on
        messageFlag = False

      else: # if HPN is off and no hold is currently active, there's no new news. Wait 60.
        print(str(time.asctime()) + ": HPN <= 300" + ", sleeping 60, HPN = " + str(HPN) + ", HPS = " + str(HPS) + ", liveHoldFlag = " + str(liveHoldFlag) + ", messageFlag = " + str(messageFlag))
        time.sleep(59)

    now = time.localtime()
    nowDay = time.strftime("%Y-%m-%d", now)
    minsSinceLaunchDayMidnight = (time.mktime(now) - time.mktime(launchDayMidnight)) / 60
    cont = (nowDay == launchDay and 270 <= minsSinceLaunchDayMidnight < 1440) or (nowDay != launchDay and 1440 <= minsSinceLaunchDayMidnight < 1710)

except Exception:
  local_functions.logfunc(logloc=logloc, line="ERROR: Problem in ecobeeOverride.py. Exiting.")
  execStr = "./prowl.sh " + "ERROR: ecobeeOverride.py has exited abnormally."
  rc = call(execStr)
  raise Exception("ERROR: Problem in ecobeeOverride.py. Exiting.")
