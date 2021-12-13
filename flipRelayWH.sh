#!/bin/bash

. $HOME/CurbAPI_profile

logfile="$CURB_LOCAL_LOG_LOC"
override_flag="${OVERRIDE_FLAG_LOC}"
now=`date '+%s'`
me=`basename $0`

# override_flag file is written by iOS Shortcut
# it contains two lines... arg=<ON or OFF>, end=timestamp
# it is deleted after a user-specified time interval (should be gone by $end timestamp)
# but that might not be 100% reliable.
if [ -f $override_flag ]; then
  . "${override_flag}"
  # if it is past the $end timestamp, the file should be gone but something happened. Delete it and run with supplied ON/OFF
  if [ ${now} -ge ${end} ]; then
    rm -f "${override_flag}"
    /usr/bin/python3 /home/pi/CurbAPI/flipRelayWH.py $1
    logFunc $me "Manual override flag present but expired. Deleting flag and operating as normal"
    exit
  else # override still in effect, so wait until override is over (+1 extra minute) and then continue
    timeToWait=$((${end}-${now}+60))
    logFunc $me "Manual override flag present, waiting ${timeToWait} seconds"
    sleep ${timeToWait}s
    logFunc $me "Done waiting, operating as normal"
    /usr/bin/python3 /home/pi/CurbAPI/flipRelayWH.py $1
  fi
else # no override in effect, so execute as normal
  /usr/bin/python3 /home/pi/CurbAPI/flipRelayWH.py $1
fi
