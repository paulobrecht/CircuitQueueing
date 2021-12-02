#!/usr/bin/python3

import json
import os
import os.path
import requests
import time
import RPi.GPIO as gpio
from io import StringIO
from local_functions import logfunc

# log file
logloc = os.environ['CURB_LOCAL_LOG_LOC']
log = open(logloc, "a")

# Access token request parameters
ATurl = "https://energycurb.auth0.com/oauth/token"
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

# write to file for re-use (expires after 24 hours)
outloc = os.environ[CURB_ACCESS_TOKEN_LOC]
outfile_exists = os.path.exists(outloc)
if outfile_exists:
  os.remove(outloc)
outfile = open(outloc, "w")
outfile.write(AT)
outfile.close()

now = time.strftime("%H:%M:%S", time.localtime())
logfunc(time=now, logloc=logloc, line="getAccessToken refreshed Curb API access token.")
