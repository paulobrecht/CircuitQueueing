#!/usr/bin/python3

import os
from time import mktime, localtime, sleep
from local_functions import newCurbQuery, parseCurb, handleException, logFunc
from json import dumps

logloc = os.environ['CURB_LOCAL_LOG_LOC']
jsonloc = os.environ['CURB_LOCAL_JSON_LOC']

now = int(mktime(localtime())) # for fetched_at

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

# output json file and log it, unless loop timed out (in which case we'd be writing the same timestamped data twice in the json file)
if i < 9:
	logFunc(now="", logloc=jsonloc, line=dumps(curb_data))
