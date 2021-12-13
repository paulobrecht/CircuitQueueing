#!/usr/bin/python3

# IMPORT
import RPi.GPIO as gpio

# mapping 0/1 to OFF/ON
map = {0:"OFF", 1:"ON"}

def getFunc():
	# GPIO setup
	WH_north, WH_south, ppump = [11, 13, 15] # board pins
	gpio.setmode(gpio.BOARD)
	gpio.setwarnings(False)
	gpio.setup(WH_north,gpio.OUT)
	gpio.setup(WH_south,gpio.OUT)
	gpio.setup(ppump,gpio.OUT)

	# Check/store initial status of each
	WHNs = map[gpio.input(WH_north)]
	WHSs = map[gpio.input(WH_south)]
	PPs  = map[gpio.input(ppump)]
#	out = "WHN="+WHNs+"&WHS="+WHSs+"&PP="+PPs
#	out = {"devices":["WHN", "WHS", "PP"], "statuses":[WHNs, WHSs, PPs]}
#	out = [WHNs, WHSs, PPs]
	out = "North WH is " + WHNs + ". South WH is " + WHSs + ". Pool pump is " + PPs + "."
	return out

m=getFunc()
print(m)
