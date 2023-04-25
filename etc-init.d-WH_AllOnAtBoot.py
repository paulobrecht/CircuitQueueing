#!/usr/bin/python3
### BEGIN INIT INFO
# Provides:          WH_AllOnAtBoot.py
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Run once at boot time to turn on all electrical panel relays
# Description:       Turns on all electrical panel relays at boot (which are later controlled by cron)
### END INIT INFO

import RPi.GPIO as gpio

#################################
# Write line to log file, default with timestamp
#################################

def logFunc(line, logloc = "/home/pi/CurbAPI/activity_log.txt", now = None):
  from time import strftime, localtime
  log = open(logloc, "a")
  now = strftime("%H:%M:%S", localtime())
  log.write(now + ": " + line + "\n")
  log.close()

# Water heater GPIO setup
WH_north, WH_south = [11, 13] # board pins
gpio.setmode(gpio.BOARD)
gpio.setwarnings(False)
gpio.setup(WH_north,gpio.OUT)
gpio.setup(WH_south,gpio.OUT)

# Turn on north only at bootup
gpio.output(WH_north,1)
gpio.output(WH_south,0)

logFunc(line = "pi-wh.lan rebooted. Restarting now with (1, 0)")
