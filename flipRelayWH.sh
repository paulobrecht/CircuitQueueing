#!/bin/bash

. $HOME/CurbAPI_profile

arg=$1
/usr/bin/python3 /home/pi/CurbAPI/flipRelayWH.py $arg
