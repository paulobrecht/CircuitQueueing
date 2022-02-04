#!/bin/bash

. $HOME/CurbAPI_profile

# kill any running copies of ecobeeOverride.py
tarm=`ps -fu pi | grep ecobeeOverride.py | grep -v "grep" | sed 's/  */ /g' | cut -f 2 -d " "`
for x in $tarm
do
  kill -3 $x
done

if [ "$#" == 1 ] && [ "$1" == "Yesterday" ]; then
  exec /home/pi/CurbAPI/ecobeeOverride.py Yesterday &
else
  exec /home/pi/CurbAPI/ecobeeOverride.py &
fi
