#!/usr/bin/python3

import os
from time import mktime, localtime, asctime, sleep, strftime, strptime
from sys import argv
from subprocess import call
from local_functions import logfunc, curbQuery, refreshEcobeeAuthToken, queryEcobee, postHold, resumeProgram, parseResponse, prowl, handleException

# env variables
CurbLocationID = os.environ["CURB_LOCATION_ID"]
CurbAPIurl = os.environ["CURB_API_URL"]
CurbAT = os.environ["CURB_ACCESS_TOKEN"]
RT = os.environ['ECOBEE_REFRESH_TOKEN']

# logloc = os.environ['CURB_LOCAL_LOG_LOC']
logloc = "/home/pi/CurbAPI/ecobee_activity_log.txt"

# convenience function logShortcut
def logShortcut (msg, hs):
  from time import asctime 

  hs_map = {1: " >  ", 0: " <= "}
  hs2 = "HPN" + hs_map[hs] + "300"
  myStr = str(asctime()) + ": " + hs2 + ", liveHoldFlag = " + str(liveHoldFlag) + ", messageFlag = " + str(messageFlag) + \
  ", HPN = " + str(HPN) + ", HPS = " + str(HPS) + ", " + msg
  return myStr



# it's impossible to kick this script off after midnight without a corrective argument
if len(argv) > 1:
  if argv[1] == "Yesterday":
    tmp = mktime(localtime()) - 86400 # 24 hours ago
    launchTime = localtime(tmp)
  else:
    raise Exception("Program argument must be 'Yesterday' or nothing at all.")
else:
  launchTime = localtime()

# log program launch
logfunc(logloc=logloc, line="ecobeeOverride launched")

# time calculations
launchDay = strftime("%Y-%m-%d", launchTime)
launchDayMidnight = strptime(launchDay + " 00:00:00", "%Y-%m-%d %H:%M:%S")

# this program runs once a day starting at 4:30 am
# So loop until 4:30 and then exit

now = localtime()
nowDay = strftime("%Y-%m-%d", now)
minsSinceLaunchDayMidnight = (mktime(now) - mktime(launchDayMidnight)) / 60

liveHoldFlag = False
messageFlag = False
cont = (nowDay == launchDay and 270 <= minsSinceLaunchDayMidnight < 1440) or (nowDay != launchDay and 1440 <= minsSinceLaunchDayMidnight < 1710)

while cont:

  # query curb for HPN (north heat pump) electricity consumption
  try:
    usage = curbQuery(locationID=CurbLocationID, apiURL=CurbAPIurl, AT=CurbAT)[0]
    HPN = usage[4]
    HPS = usage[3]
    totalHogConsumption = sum(usage[0:3] + usage[4:]) # exclude HPS because that's the one we're overriding
  except Exception:
    handleException(msg="Problem with curbQuery() in ecobeeOverride.py", logloc=logloc)

  # if HPN is on and no hold is currently active, set an override hold on the ecobee for holdInterval (default=4) minutes
  if HPN > 300 or totalHogConsumption > 10000:

    hs = 1
    if liveHoldFlag == False:

      # update ecobee access token
      try:
        jkey = refreshEcobeeAuthToken(refresh_token=RT)
        ECOBEE_TOKEN, ECOBEE_TOKEN_TYPE, ECOBEE_REFRESH_TOKEN, ECOBEE_TOKEN_EXPIRY, ECOBEE_SCOPE2 = jkey.values()
        logfunc(logloc=logloc, line=logShortcut(msg = "ran refreshEcobeeAuthToken (1)", hs = hs))
      except Exception:
        handleException(msg="Problem refreshing Ecobee token (1) using refresh token in ecobeeOverride.py", logloc=logloc)

      # query thermostats to get necessary data fields
      try:
        temps, thermostatTime = queryEcobee(auth_token=ECOBEE_TOKEN)
        logfunc(logloc=logloc, line=logShortcut(msg = "ran queryEcobee()", hs = hs))
      except Exception:
        handleException(msg="Problem querying ecobee to get temps and time", logloc=logloc)

      # Run setHold function
      try:
        setHold, endEpoch, resultAPI = postHold(auth_token=ECOBEE_TOKEN, thermostatTime=thermostatTime, heatRangeLow=temps[0], coolRangeHigh=temps[1])
        logfunc(logloc=logloc, line=logShortcut(msg = "ran postHold()", hs = hs))
        if resultAPI[3] != 200:
          logfunc(logloc=logloc, line=logShortcut(msg=resultAPI[0] + " received a non-200 response (" + str(resultAPI[3]) + ")", hs = hs))
      except Exception:
        handleException(msg="Problem with setHold in ecobeeOverride.py", logloc=logloc)

      # log the override (if this is the first time through the loop with HPN on)
      if messageFlag == False:
        logfunc(logloc=logloc, line="North heat pump is running, setting an override hold on south heat pump")
        messageFlag = True

      # set live hold flag to indicate active hold
      liveHoldFlag = True

    else: # if HPN is on and liveHoldFlag is already True, there's no new news. Wait 30 or until expiry
      remainingHold = endEpoch - mktime(now)
      if remainingHold <= 30:
        logfunc(logloc = logloc, line = logShortcut(msg="sleeping" + remainingHold, hs = hs))
        sleep(remainingHold)
        liveHoldFlag = False
      else:
        logfunc(logloc = logloc, line = logShortcut(msg = "sleeping 30", hs = hs))
        sleep(29)

  else: # if HPN is not on (<= 300)

    hs = 0
    if liveHoldFlag == True: # if HPN is off but live hold flag is set, we are first detecting that HPN has ended. Resume program, set live hold flag to false.

      # update ecobee access token
      try:
        jkey = refreshEcobeeAuthToken(refresh_token=RT)
        ECOBEE_TOKEN, ECOBEE_TOKEN_TYPE, ECOBEE_REFRESH_TOKEN, ECOBEE_TOKEN_EXPIRY, ECOBEE_SCOPE2 = jkey.values()
        logfunc(logloc=logloc, line=logShortcut(msg = "ran refreshEcobeeAuthToken (2)", hs = hs))
      except Exception:
        handleException(msg="Problem refreshing Ecobee token (2) using refresh token", logloc=logloc)

      # resume program (cancel hold)
      try:
        rP, resultAPI = resumeProgram(auth_token=ECOBEE_TOKEN)
        logfunc(logloc = logloc, line = logShortcut(msg = "ran resumeProgram()", hs = hs))
        if resultAPI[3] != 200:
          logfunc(logloc=logloc, line=logShortcut(msg=resultAPI[0] + " received a non-200 response (" + str(resultAPI[3]) + ")", hs = hs))
      except Exception:
        handleException(msg="Problem cancelling hold in ecobeeOverride.py", logloc=logloc)

      # log the resumption (since is the first loop detecting cessation of HPN activity)
      logfunc(logloc=logloc, line="North heat pump no longer running, allowing south heat pump (ecobee) to resume program")

      # set live hold flag to indicate no active hold
      liveHoldFlag = False

      # set messageFlag to false so log message is written next time HPN kicks on
      messageFlag = False

    else: # if HPN is off and no hold is currently active, there's no new news. Wait 60.
      logfunc(logloc=logloc, line=logShortcut(msg = "sleeping 60", hs = hs))
      sleep(59)

  now = localtime()
  nowDay = strftime("%Y-%m-%d", now)
  minsSinceLaunchDayMidnight = (mktime(now) - mktime(launchDayMidnight)) / 60
  cont = (nowDay == launchDay and 270 <= minsSinceLaunchDayMidnight < 1440) or (nowDay != launchDay and 1440 <= minsSinceLaunchDayMidnight < 1710)

