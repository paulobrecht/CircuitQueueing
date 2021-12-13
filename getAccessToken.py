#!/usr/bin/python3

import json
import os
import os.path
import requests
import time
import RPi.GPIO as gpio
from local_functions import logfunc

# Access token request parameters
ATurl = os.environ['CURB_TOKEN_URL']
payload = {"grant_type": "password",
           "audience": os.environ['CURB_QUERY_AUDIENCE'],
           "username": os.environ['CURB_QUERY_USERNAME'],
           "password": os.environ['CURB_QUERY_PASSWORD'],
           "client_id": os.environ['CURB_QUERY_CLIENT_ID'],
           "client_secret": os.environ['CURB_QUERY_CLIENT_SECRET']}
headers = {'content-type: application/json','cache-control: no-cache', 'accept-charset: UTF-8'}

# send request for access token
key = requests.post(ATurl, json=payload)

# parse response to pull out token
jkey = json.loads(key.text)
AT = jkey["access_token"]

# log file
now = time.strftime("%H:%M:%S", time.localtime())
logloc = os.environ['CURB_LOCAL_LOG_LOC']

# write AT to file for re-use (expires after 24 hours)
outloc = os.environ['CURB_ACCESS_TOKEN_LOC']
try:
  os.remove(outloc)
except FileNotFoundError:
  pass
except:
  logfunc(logloc=logloc, line=str(now + ": ERROR: Problem with removal of previous access token file. Trying to continue..."))

try:
  outfile = open(outloc, "w")
  outfile.write(AT)
  outfile.close()
except:
  logfunc(logloc=logloc, line=str(now + ": ERROR: Could not replace access token."))
  raise SystemExit(str(now + ": ERROR: Could not replace access token."))
else:
  logfunc(logloc=logloc, line="getAccessToken refreshed Curb API access token.")
