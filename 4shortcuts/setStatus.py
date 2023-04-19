#!/usr/bin/python3

# IMPORT
import RPi.GPIO as gpio
import sys

# mapping OFF/ON to 0/1
unmap = {"OFF":0, "ON":1}

arg = sys.argv[1]

# GPIO setup
WH_north, WH_south = [11, 13] # board pins
gpio.setmode(gpio.BOARD)
gpio.setwarnings(False)
gpio.setup(WH_north,gpio.OUT)
gpio.setup(WH_south,gpio.OUT)

# turn all on or off, depending on argument
act = unmap[arg]
gpio.output(WH_north, act)
gpio.output(WH_south, act)
