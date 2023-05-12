#!/bin/bash
# this script counts Curb fetch errors in activity_log.txt and alerts if they are recurring

# activity file
act=$CURB_LOCAL_LOG_LOC

# get and count errors
errors=( $(cat $act | grep "Error fetching Curb consumption data" | cut -c1-8) ) # get errors (times only) as array
errorCount=${#errors[@]}

# for prowl
timestamps=$(for error in ${errors[@]:$errorCount-5:4}; do echo -n "$error, "; done; echo -n "${errors[$errorCount-1]}")
app="ConnectCheck"
event="Repeated Curb query failures"
desc="Curb query has failed ${errorCount} times today (last 5 at $timestamps)" # for prowl

if [[ $errorCount -ge 5 ]]; then
  ./prowl.sh "$desc" "$app"
  prc=$?
else
  prc=0
fi

xrc=$prc

if [[ $prc != 0 ]]; then
  echo "prowl script did not receive a 200 reply."
  xrc=2
fi

exit $xrc
