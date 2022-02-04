import os
key = os.environ['ECOBEE_API_KEY']




def getEcobeePin(key=key, headers={'content-type': 'application/json', 'charset': 'UTF-8'}):
  import json
  import requests

  payload = {"response_type": "ecobeePin", "client_id": key, "scope": "smartWrite"}
  pin = requests.get("https://api.ecobee.com/authorize", params=payload, headers=headers)
  jpin = json.loads(pin.text)
  return jpin

# jpin = getEcobeePin()
# ECOBEE_PIN, ECOBEE_PIN_CODE, ECOBEE_PIN_INTERVAL, ECOBEE_PIN_EXPIRY, ECOBEE_PIN_SCOPE = jpin.values()




def getEcobeeAuthToken(pin, key=key, headers={'content-type': 'application/json', 'charset': 'UTF-8'}):
  import json
  import requests

  payload = {"grant_type": "ecobeePin", "code": pin, "client_id": key}
  key = requests.post("https://api.ecobee.com/token", params=payload, headers=headers)
  jkey = json.loads(key.text)

  # write refresh token to file
  outloc = os.environ['ECOBEE_REFRESH_TOKEN_LOC']
  try:
    os.remove(outloc)
  except FileNotFoundError:
    pass
  except Exception:
    logfunc(logloc=logloc, line=str("ERROR: Problem with removal of previous ecobee refresh token file. Trying to continue..."))

  try:
    ECOBEE_REFRESH_TOKEN = jkey['refresh_token']
    outfile = open(outloc, "w")
    outfile.write(ECOBEE_REFRESH_TOKEN)
    outfile.close()
  except Exception:
    logfunc(logloc=logloc, line=str("ERROR: Could not replace ecobee refresh token."))
    raise SystemExit(str("ERROR: Could not replace ecobee refresh token."))
  else:
    logfunc(logloc=logloc, line="getEcobeeAuthToken() refreshed ecobee refresh token token.")

  return jkey

# jkey = getEcobeeAuthToken(pin=ECOBEE_PIN, key=os.environ['ECOBEE_API_KEY'])
# ECOBEE_TOKEN, ECOBEE_TOKEN_TYPE, ECOBEE_TOKEN_EXPIRY, ECOBEE_SCOPE2, ECOBEE_REFRESH_TOKEN = jkey.values()




# Refresh authorization token
def refreshEcobeeAuthToken(refresh_token, key=key, headers={'content-type': 'application/json', 'charset': 'UTF-8'}):
  import json
  import requests

  payload = {"grant_type": "refresh_token", "refresh_token": refresh_token, "client_id": key}
  key = requests.post("https://api.ecobee.com/token", params=payload, headers=headers)
  jkey = json.loads(key.text)
  return jkey

# jkey = refreshEcobeeAuthToken(refresh_token=os.environ['ECOBEE_REFRESH_TOKEN'])
# ECOBEE_TOKEN, ECOBEE_TOKEN_TYPE, ECOBEE_REFRESH_TOKEN, ECOBEE_TOKEN_EXPIRY, ECOBEE_SCOPE2 = jkey.values()



# query (requires adding authorization header)
def queryEcobee(auth_token, includeSettings=True, includeEvents=False, headers={'content-type': 'application/json', 'charset': 'UTF-8'}):
  import json
  import requests

  tokenstr = "Bearer " + auth_token
  headers.update(Authorization = tokenstr)

  if includeSettings == includeEvents or includeSettings not in [True, False] or includeEvents not in [True, False]:
    raise Exception("Exactly one of includeSettings or includeEvents must be True, both must be populated (boolean).")

  if includeSettings==True:
    # get extremes of heat and cool ranges
    payload = {'body': '{"selection": {"selectionType": "registered", "selectionMatch": "", "includeSettings": "true"}}'}
    tstat = requests.get('https://api.ecobee.com/1/thermostat', headers=headers, params=payload)

    # extract the two extreme temps
    settings = json.loads(tstat.text)['thermostatList'][0]['settings']
    thermostatTime = json.loads(tstat.text)['thermostatList'][0]['thermostatTime']
    temps = [settings[x] for x in ['heatRangeLow', 'coolRangeHigh']]
    return temps, thermostatTime
  else:
    payload = {'body': '{"selection": {"selectionType": "registered", "selectionMatch": "", "includeEvents": "true"}}'}
    tstat = requests.get('https://api.ecobee.com/1/thermostat', headers=headers, params=payload)
    return tstat




# post hold
def postHold(auth_token, thermostatTime, heatRangeLow, coolRangeHigh, holdInterval=240, headers={'content-type': 'application/json', 'charset': 'UTF-8'}):
  import json
  import requests
  import time

  tokenstr = "Bearer " + auth_token
  headers.update(Authorization = tokenstr)

  nowStrp = time.mktime(time.strptime(thermostatTime, "%Y-%m-%d %H:%M:%S"))
  end = time.localtime(nowStrp + holdInterval)
  endEpoch = time.mktime(end)
  endDate = time.strftime("%Y-%m-%d", end)
  endTime = time.strftime("%H:%M:%S", end)
  setHoldSelection = {'selectionType':'registered','selectionMatch':''}
  setHoldParams = {'holdType':'dateTime', 'endDate':endDate, 'endTime':endTime,'heatHoldTemp':heatRangeLow,'coolHoldTemp':coolRangeHigh}
  msgParams = {"text": "On hold, waiting for other heat pump to finish."}
  setHoldJSON = {'selection': setHoldSelection, 'functions':[{'type':'setHold', 'params':setHoldParams}, {"type":"sendMessage","params":msgParams}]}

  setHold = requests.post('https://api.ecobee.com/1/thermostat', headers=headers, json=setHoldJSON)
  resultAPI = parseResponse(setHold)
  return setHold, endEpoch, resultAPI




# resume program (end hold)
def resumeProgram(auth_token, headers={'content-type': 'application/json', 'charset': 'UTF-8'}):
  import json
  import requests

  tokenstr = "Bearer " + auth_token
  headers.update(Authorization = tokenstr)

  rP_Selection = {'selectionType':'registered','selectionMatch':''}
  rP_Params = {"resumeAll":"false"}
  msgParams = {"text": "Other heat pump has finished. Resuming schedule."}
  rP_json = {'selection': rP_Selection, 'functions':[{'type':'resumeProgram','params':rP_Params},{"type":"sendMessage","params":msgParams}]}
  rP = requests.post('https://api.ecobee.com/1/thermostat', headers=headers, json=rP_json)
  resultAPI = parseResponse(rP)
  return rP, resultAPI




# parse ecobee API replies
def parseResponse(item):
  import json
  import inspect
  import local_functions
  test = json.loads(item.text)
  obj = json.loads(item.text)['status']
  statusCode = obj['code'] # 0 on success
  statusMessage = obj['message'] # "" on success
  statusCodeHTTP = item.status_code # 200 (possibly 2XX?) on success
  statusOK = item.ok # "True" on success

  caller = inspect.stack()[1].function
  parseObj = (caller, statusCode, statusMessage, statusCodeHTTP, statusOK)
  return parseObj
