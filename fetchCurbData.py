#!/usr/bin/python3

import os
from time import mktime, localtime, sleep, strftime
from local_functions import prowl, newCurbQuery, parseCurb, handleException, logFunc
from json import dumps

logloc = os.environ['CURB_LOCAL_LOG_LOC']
jsonloc = os.environ['CURB_LOCAL_JSON_LOC']

# fetch data
try:
	curb_data = newCurbQuery()
except BaseException:
	handleException(msg="Error fetching Curb consumption data", logloc=logloc)

# counter for retry up ahead
i=0

# look at data lag, refetch if it's stale
first_curb_timestamp = curb_data['timestamp']
data_lag = curb_data['data_lag']
if data_lag > 120:
	while i < 9:
		sleep(5)
		curb_data = newCurbQuery()
		if curb_data['timestamp'] > first_curb_timestamp:
			break
		else:
			i += 1

# output json to file, unless loop timed out (in which case we'd be writing the same timestamped data twice in the json file)
if i < 9:
	logFunc(now="", logloc=jsonloc, line=dumps(curb_data))




# -------------------------------
# track water heater last-on time
# -------------------------------
def writeFile(fr):
	file = open(fr, "w")
	file.write(f"{now}\n")
	file.close()

def timeSince(fr, now):
	with open(fr) as file:
		for line in file:
			pass
		lastOn = int(line)
	timeSince = int(now) - lastOn
	if fr == whnFile:
		dev = "north water heater"
	elif fr == whsFile:
		dev = "south water heater"
	else:
		dev = "(unknown device)"

	rv = True
	msgStr = ""

	# 57,600 is 14 hours. Every weeknight, south is off from 11 pm until after 11 am,
	# and there may be a queue at 11 am, so have to wait this long
	if timeSince > 57600:
		rv = False
		msgStr = dev + " has not run for " + str(int(timeSince/60)) + " min (" + str(int(timeSince/3600)) + " hours)."
	return rv, msgStr

now = str(curb_data['timestamp'])
thisMinute = int(strftime("%M", localtime(int(now))))

# last-on filenames
whnFile = os.environ['CURB_DIR'] + "textfiles/whnLastOn.txt"
whsFile = os.environ['CURB_DIR'] + "textfiles/whsLastOn.txt"

# update WHN file
if curb_data['Water Heater North'] > 500:
	writeFile(whnFile)
elif thisMinute in range(0,60,10): # read files on the tens and prowl/mail if it's been more than 8 hours since a water heater ran
	stat1, msg1 = timeSince(fr=whnFile, now=now)
	if stat1 == False:
		handleException(msg=msg1, logloc=logloc, errorcode=msg1)

# update WHS file
if curb_data['Water Heater South'] > 500:
	writeFile(whsFile)
elif thisMinute in range(0,60,10): # read files on the tens and prowl/mail if it's been more than 8 hours since a water heater ran
	stat2, msg2 = timeSince(fr=whsFile, now=now)
	if stat2 == False:
		handleException(msg=msg2, logloc=logloc, errorcode=msg2)
