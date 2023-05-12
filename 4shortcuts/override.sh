#!/bin/bash

# When executed (e.g., by iOS Shortcuts), a file is written that the other CurbAPI programs look for.
# If the file is present and the timestamp is not in the past, other programs exit without making changes
# File contents:
# line 1: ON or OFF
# line 2: timestamp at which override ends

# Sample call: ./override.sh ON 60

logfile="$CURB_LOCAL_LOG_LOC"
dt=`date +'%H:%M:%S'` # HMS right now
me=`basename $0`

[[ -f ${OVERRIDE_FLAG_LOC} ]] && rm -f ${OVERRIDE_FLAG_LOC}

echo "# File generated by $me at $dt" > ${OVERRIDE_FLAG_LOC}
echo "arg=${1}" >> ${OVERRIDE_FLAG_LOC}
echo ""end=`date -d "+${2} minutes" "+%s"`"" >> ${OVERRIDE_FLAG_LOC}
echo ""# for humans, end = `date -d "+${2} minutes" "+%H:%M:%S"`"" >> ${OVERRIDE_FLAG_LOC}

logFunc $me "Manual override, turning water heaters ${1} for ${2} minutes"
$HOME/CurbAPI/4shortcuts/setStatus.py ${1}
sleep ${2}m
logFunc $me "Manual override expired"

rm -f ${OVERRIDE_FLAG_LOC}

# if it's during peak hours, nothing will run to undo the override.
# Removing the flag is not enough, so do this manually.
[[ ${1} -eq OFF ]] && newset=ON
[[ ${1} -eq ON ]] && newset=OFF

hiver=(10 11 12 01 02 03 04) # months
ete=(05 06 07 08 09) # months

hour=$(date +"%H")
month=$(date +"%m")

if [[ "${hiver[*]}" =~ "${month}" ]]; then
  peak_hours=(06 07 08 18 19 20)
elif [[ "${ete[*]}" =~ "${month}" ]]; then
  peak_hours=(15 16 17 18)
fi

if [[ "${peak_hours[*]}" =~ "${hour}" ]]; then
  $HOME/CurbAPI/4shortcuts/setStatus.py ${newset}
fi

exit
