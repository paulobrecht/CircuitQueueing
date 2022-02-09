#!/usr/bin/python3

import os
from json import loads
from requests import post
from time import strftime, localtime
from local_functions import logFunc

logloc = os.environ['CURB_LOCAL_LOG_LOC']
outloc = os.environ['CURB_ACCESS_TOKEN_LOC']

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
key = post(ATurl, json=payload)

# parse response in order to pull out token
jkey = loads(key.text)
AT = jkey["access_token"]

# write AT to file for re-use (expires after 24 hours)
try:
  os.remove(outloc)
except FileNotFoundError:
  pass
except:
  logFunc(logloc=logloc, line="ERROR: Problem with removal of previous Curb access token file. Trying to continue...")

try:
  outfile = open(outloc, "w")
  outfile.write(AT)
  outfile.close()
except:
  logFunc(logloc=logloc, line="ERROR: Could not replace Curb access token.")
  raise SystemExit("ERROR: Could not replace Curb access token")
else:
  logFunc(logloc=logloc, line="Refreshed Curb API access token")
