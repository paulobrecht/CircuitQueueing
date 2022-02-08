#!/bin/bash

. $HOME/CurbAPI_profile

# kill any running copies of ecobeeOverride.py
tmar=$(ps axf | grep ecobeeOverride.py | grep -v "grep" | grep -v "nano" | awk '{print $1}')
for x in $tarm
do
  kill -9 $x
done

/home/pi/CurbAPI/ecobeeOverride.py &
