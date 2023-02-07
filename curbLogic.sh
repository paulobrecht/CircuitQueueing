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
  if [ ${now} -gt ${end} ]; then
    rm -f "${override_flag}"
	/usr/bin/python3 /home/pi/CurbAPI/curbLogic.py
    logFunc $me "Manual override flag present but expired. Deleting flag and operating as normal"
    exit
  else # override still in effect, so exit... every launched curbLogic.sh will exit until override flag is removed or expired
    exit
  fi
else # no override in effect, so execute as normal
  /usr/bin/python3 /home/pi/CurbAPI/curbLogic.py
fi

