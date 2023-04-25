#!/usr/bin/python3

# IMPORT
import RPi.GPIO as gpio
import sys
import time
import local_functions as LF
import os

# GPIO setup
WH_north, WH_south = [11, 13] # board pins
gpio.setmode(gpio.BOARD)
gpio.setwarnings(False)
gpio.setup(WH_north,gpio.OUT)
gpio.setup(WH_south,gpio.OUT)

# log
logloc = os.environ['CURB_LOCAL_LOG_LOC']


LF.logFunc(logloc=logloc, line="North water heater allowed for one hour for morning shower")
gpio.output(WH_north, 1)
gpio.output(WH_south, 0)
time.sleep(35400)
LF.logFunc(logloc=logloc, line="North water heater shower time is over")
gpio.output(WH_north, 0)
