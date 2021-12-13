#!/bin/bash

. $HOME/CurbAPI_profile

override_flag="${OVERRIDE_FLAG_LOC}"
logfile="$CURB_LOCAL_LOG_LOC"
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
    logFunc $me "Manual override flag present but expired. Deleting flag and operating as normal"
    /usr/bin/python3 /home/pi/CurbAPI/queryCurb.py
    exit
  else # override still in effect, so exit, do not query of change status of anything
    endHR=`date --date="@$end" '+%H:%M:%S'`
    logFunc $me "Manual override flag present, scheduled to expire at $endHR, exiting"
    exit
  fi
else # no override in effect, so execute as normal
  /usr/bin/python3 /home/pi/CurbAPI/queryCurb.py
fi
