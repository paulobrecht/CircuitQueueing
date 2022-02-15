#!/bin/bash

. $HOME/CurbAPI_profile

# # kill any running copies of ecobeeOverride.py
# tmar=$(ps axf | grep ecobeeOverride.py | grep -v "grep" | grep -v "nano" | awk '{print $1}')
# for x in $tarm
# do
#   kill -9 $x
# done

# if ecobeeOverride.py is already running then don't launch it
# but now silently, in order to avoid cron emails
ncop=$(ps -fA | grep ecobeeOverride.py | grep "/usr/bin/python3 /home/pi/CurbAPI/ecobeeOverride.py" | grep -v grep | wc -l)
if [[ $ncop -eq 0 ]]; then
  exec /home/pi/CurbAPI/ecobeeOverride.py &
fi
