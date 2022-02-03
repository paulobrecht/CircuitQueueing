#!/usr/bin/python3

try:
  import os
  import time
  import local_functions
  import ecobee_functions

  # time calculations
  launchTime = time.localtime()
  launchDay = time.strftime("%Y-%m-%d", launchTime)
  launchDayMidnight = time.strptime(launchDay + " 00:00:00", "%Y-%m-%d %H:%M:%S")

  # env variables
  CurbLocationID = os.environ["CURB_LOCATION_ID"]
  CurbAPIurl = os.environ["CURB_API_URL"]
  logloc = os.environ['CURB_LOCAL_LOG_LOC']
  CurbAT = os.environ["CURB_ACCESS_TOKEN"]
  RT = os.environ['ECOBEE_REFRESH_TOKEN']

  # this program runs once a day starting at 4:30 am
  # So loop until 4:28 and then exit

  now = time.localtime()
  nowDay = time.strftime("%Y-%m-%d", now)
  minsSinceLaunchDayMidnight = (time.mktime(now) - time.mktime(launchDayMidnight)) / 60

  liveHoldFlag = False
  cont = (nowDay == launchDay and 270 <= minsSinceLaunchDayMidnight < 1440) or (nowDay != launchDay and minsSinceLaunchDayMidnight <= 268)
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

    # if HPN is on and no hold is currently active, set an overridehold on the ecobee for 5 minutes
    if HPN > 300:

      if liveHoldFlag == False:

        # update ecobee access token
        try:
          jkey = ecobee_functions.refreshEcobeeAuthToken(refresh_token=RT)
          ECOBEE_TOKEN, ECOBEE_TOKEN_TYPE, ECOBEE_REFRESH_TOKEN, ECOBEE_TOKEN_EXPIRY, ECOBEE_SCOPE2 = jkey.values()
        except Exception:
          local_functions.logfunc(logloc=logloc, line="ERROR: Problem refreshing Ecobee token (1) using refresh token in ecobeeOverride.py. Exiting.")
          execStr = "./prowl.sh " + "ERROR: ecobeeOverride.py has exited abnormally."
          rc = call(execStr)
          raise Exception("ERROR: Problem refreshing Ecobee token (1) using refresh token in ecobeeOverride.py. Exiting.")

        # query thermostats to get necessary data fields
        try:
          temps, thermostatTime = ecobee_functions.queryEcobee(auth_token=ECOBEE_TOKEN)
        except Exception:
          local_functions.logfunc(logloc=logloc, line="ERROR: Problem querying ecobee to get temps and time in ecobeeOverride.py. Exiting.")
          execStr = "./prowl.sh " + "ERROR: ecobeeOverride.py has exited abnormally."
          rc = call(execStr)
          raise Exception("ERROR: Problem querying ecobee to get temps and time in ecobeeOverride.py. Exiting.")

        # Run setHold function
        try:
          setHold, endEpoch = ecobee_functions.postHold(auth_token=ECOBEE_TOKEN, thermostatTime=thermostatTime, heatRangeLow=temps[0], coolRangeHigh=temps[1])
          # # have to handle non-200 response codes here
        except Exception:
          local_functions.logfunc(logloc=logloc, line="ERROR: Problem with setHold in ecobeeOverride.py. Exiting.")
          execStr = "./prowl.sh " + "ERROR: ecobeeOverride.py has exited abnormally."
          rc = call(execStr)
          raise Exception("ERROR: Problem with setHold in ecobeeOverride.py. Exiting.")

        # log the override (since is the first loop during this HPN activity)
        local_functions.logfunc(logloc=logloc, line="North heat pump is running, setting an override hold on south heat pump")

        # set live hold flag to indicate active hold
        liveHoldFlag = True

      else: # if HPN is on and liveHoldFlag is already True, there's no new news. Wait 30 or until expiry
        remainingHold = endEpoch - time.mktime(now)
        if remainingHold < 30:
          time.sleep(remainingHold)
          liveHoldFlag = False

    else: # if HPN is not on (<= 300)

      if liveHoldFlag == True: # if HPN is off but live hold flag is set, we are just detecting that HPN has ended. Resume program and set live hold flag to false.

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
          # # have to handle non-200 responses here
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

      else: # if HPN is off and no hold is currently active, there's no new news. Wait 60.
        time.sleep(60)

    now = time.localtime()
    nowDay = time.strftime("%Y-%m-%d", now)
    minsSinceLaunchDayMidnight = (time.mktime(now) - time.mktime(launchDayMidnight)) / 60
    cont = (nowDay == launchDay and 270 <= minsSinceLaunchDayMidnight < 1440) or (nowDay != launchDay and minsSinceLaunchDayMidnight <= 268)

except Exception:
  local_functions.logfunc(logloc=logloc, line="ERROR: Problem in ecobeeOverride.py. Exiting.")
  execStr = "./prowl.sh " + "ERROR: ecobeeOverride.py has exited abnormally."
  rc = call(execStr)
  raise Exception("ERROR: Problem in ecobeeOverride.py. Exiting.")
