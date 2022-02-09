#!/usr/bin/python3

import os
from local_functions import newCurbQuery, parseCurb, handleException, logFunc
from json import dumps

logloc = os.environ['CURB_LOCAL_LOG_LOC']
jsonloc = os.environ['CURB_LOCAL_JSON_LOC']

try:
	curb_data = newCurbQuery()
except BaseException:
	handleException(msg="Error fetching Curb consumption data", logloc=logloc)

# output json file and log it
logFunc(now="", logloc=jsonloc, line=dumps(curb_data))
