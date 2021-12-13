#!/bin/bash

. $HOME/CurbAPI_profile

logfile="$CURB_LOCAL_LOG_LOC"
override_flag="${OVERRIDE_FLAG_LOC}"
dt=`date +'%H:%M:%S'` # HMS right now
me=`basename $0`

[ -f ${override_flag} ] && rm -f ${override_flag}

echo "# File generated by $me at $dt" > ${override_flag}
echo "arg=${1}" >> ${override_flag}
echo ""end=`date -d "+${2} minutes" "+%s"`"" >> ${override_flag}

logFunc $me "Manual override, turning water heaters and pool pump ${1} for ${2} minutes"
[ $1 == "ON" ] && $HOME/CurbAPI/4shortcuts/setStatus.py ON
[ $1 == "OFF" ] && $HOME/CurbAPI/4shortcuts/setStatus.py OFF
sleep ${2}m
logFunc $me "Manual override expired"

rm -f ${override_flag}
exit
