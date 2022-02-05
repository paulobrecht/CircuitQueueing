# import os because a default function arg in some ecobee functions requires os.environ
import os

#################################
# Write line to log file, default with timestamp
#################################

def logfunc(logloc, line, now = None):
  from time import strftime, localtime

  log = open(logloc, "a")
  if now is None:
    now = strftime("%H:%M:%S", localtime())
    log.write(now + ": " + line + "\n")
  elif now  == "":
    log.write(line + "\n")
  else:
    log.write(now + ": " + line + "\n")
  log.close()


#################################
# Curb query (get usage)
#################################

def curbQuery(locationID, apiURL, AT):

  from json import loads
  from requests import get
  import os

  # get latest usage data using daily token
  Lurl = apiURL + locationID
  bearer_string = 'Bearer ' + AT
  headers = {'authorization': bearer_string, 'Keep-Alive': 'timeout=110, max=10'}
  latest = get(Lurl, headers=headers)
  latest.close()

  # parse latest usage data ("log" is defined in calling script)
  latest_json = loads(latest.text)
  try:
    circuits = latest_json["circuits"]
  except BaseException as err:
    message = str(err) + " ---  " + str(type(err)) + " --- " + latest.text
    outval = ["ERROR", message]
  else:
    length = len(circuits)
    for i in range(length):
      this_circuit = circuits[i]
      if "label" in this_circuit.keys():
        this_label = this_circuit["label"]
        if this_label.upper() == "WATER HEATER SOUTH":
          WHS = this_circuit["w"]
        elif this_label.upper() == "WATER HEATER NORTH":
          WHN = this_circuit["w"]
        elif this_label.upper() == "DRYER 1":
          DRY1 = this_circuit["w"]
        elif this_label.upper() == "DRYER 2":
          DRY2 = this_circuit["w"]
        elif this_label.upper() == "HEAT PUMP SOUTH":
          HPS = this_circuit["w"]
        elif this_label.upper() == "HEAT PUMP NORTH":
          HPN = this_circuit["w"]
        elif this_label.upper() == "SUB PANEL 1":
          SUB1 = this_circuit["w"]
        elif this_label.upper() == "SUB PANEL 2":
          SUB2 = this_circuit["w"]
        elif this_label.upper() == "POOL PUMP 1":
          PP1 = this_circuit["w"]
        elif this_label.upper() == "POOL PUMP 2":
          PP2 = this_circuit["w"]
    SUB = SUB1 + SUB2
    DRY = DRY1 + DRY2
    PP = PP1 + PP2
    usage_tuple = (WHS, WHN, DRY, HPS, HPN, SUB, PP)
    outval = [usage_tuple, latest_json]
  return outval


#################################
# Get ecobee pin
#################################
def getEcobeePin(key=os.environ['ECOBEE_API_KEY'], headers={'content-type': 'application/json', 'charset': 'UTF-8'}):
  from json import loads
  from requests import get

  payload = {"response_type": "ecobeePin", "client_id": key, "scope": "smartWrite"}
  pin = get("https://api.ecobee.com/authorize", params=payload, headers=headers)
  jpin = loads(pin.text)
  return jpin

# jpin = getEcobeePin()
# ECOBEE_PIN, ECOBEE_PIN_CODE, ECOBEE_PIN_INTERVAL, ECOBEE_PIN_EXPIRY, ECOBEE_PIN_SCOPE = jpin.values()


#################################
# Get ecobee auth token (using pin)
#################################

def getEcobeeAuthToken(pin, key=os.environ['ECOBEE_API_KEY'], headers={'content-type': 'application/json', 'charset': 'UTF-8'}):
  from json import loads
  from requests import post
  from local_functions import logfunc

  payload = {"grant_type": "ecobeePin", "code": pin, "client_id": key}
  response = post("https://api.ecobee.com/token", params=payload, headers=headers)
  jkey = loads(response.text)

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


#################################
# Refresh ecobee auth token (using refresh token)
#################################

def refreshEcobeeAuthToken(refresh_token, key=os.environ['ECOBEE_API_KEY'], headers={'content-type': 'application/json', 'charset': 'UTF-8'}):
  from requests import post
  from json import loads

  payload = {"grant_type": "refresh_token", "refresh_token": refresh_token, "client_id": key}
  response = post("https://api.ecobee.com/token", params=payload, headers=headers)
  jkey = loads(response.text)
  return jkey

# jkey = refreshEcobeeAuthToken(refresh_token=os.environ['ECOBEE_REFRESH_TOKEN'])
# ECOBEE_TOKEN, ECOBEE_TOKEN_TYPE, ECOBEE_REFRESH_TOKEN, ECOBEE_TOKEN_EXPIRY, ECOBEE_SCOPE2 = jkey.values()



#################################
# ecobee /thermostat query
#################################

def queryEcobee(auth_token, includeSettings=True, includeEvents=False, headers={'content-type': 'application/json', 'charset': 'UTF-8'}):
  from json import loads
  from requests import get

  tokenstr = "Bearer " + auth_token
  headers.update(Authorization = tokenstr)

  if includeSettings == includeEvents or includeSettings not in [True, False] or includeEvents not in [True, False]:
    raise Exception("Exactly one of includeSettings or includeEvents must be True, both must be populated (boolean).")

  if includeSettings==True:
    # get extremes of heat and cool ranges
    payload = {'body': '{"selection": {"selectionType": "registered", "selectionMatch": "", "includeSettings": "true"}}'}
    tstat = get('https://api.ecobee.com/1/thermostat', headers=headers, params=payload)

    # extract the two extreme temps
    settings = loads(tstat.text)['thermostatList'][0]['settings']
    thermostatTime = loads(tstat.text)['thermostatList'][0]['thermostatTime']
    temps = [settings[x] for x in ['heatRangeLow', 'coolRangeHigh']]
    return temps, thermostatTime
  else:
    payload = {'body': '{"selection": {"selectionType": "registered", "selectionMatch": "", "includeEvents": "true"}}'}
    tstat = get('https://api.ecobee.com/1/thermostat', headers=headers, params=payload)
    return tstat


#################################
# ecobee post hold
#################################

def postHold(auth_token, thermostatTime, heatRangeLow, coolRangeHigh, holdInterval=240, headers={'content-type': 'application/json', 'charset': 'UTF-8'}):
  from requests import post
  from time import mktime, localtime, strftime, strptime

  tokenstr = "Bearer " + auth_token
  headers.update(Authorization = tokenstr)

  nowStrp = mktime(strptime(thermostatTime, "%Y-%m-%d %H:%M:%S"))
  end = localtime(nowStrp + holdInterval)
  endEpoch = mktime(end)
  endDate = strftime("%Y-%m-%d", end)
  endTime = strftime("%H:%M:%S", end)
  setHoldSelection = {'selectionType':'registered','selectionMatch':''}
  setHoldParams = {'holdType':'dateTime', 'endDate':endDate, 'endTime':endTime,'heatHoldTemp':heatRangeLow,'coolHoldTemp':coolRangeHigh}
  msgParams = {"text": "On hold, waiting for other heat pump to finish."}
  setHoldJSON = {'selection': setHoldSelection, 'functions':[{'type':'setHold', 'params':setHoldParams}, {"type":"sendMessage","params":msgParams}]}

  setHold = post('https://api.ecobee.com/1/thermostat', headers=headers, json=setHoldJSON)
  resultAPI = parseResponse(setHold)
  return setHold, endEpoch, resultAPI


#################################
# ecobee resume program (end hold)
#################################

def resumeProgram(auth_token, headers={'content-type': 'application/json', 'charset': 'UTF-8'}):
  from requests import post

  tokenstr = "Bearer " + auth_token
  headers.update(Authorization = tokenstr)

  rP_Selection = {'selectionType':'registered','selectionMatch':''}
  rP_Params = {"resumeAll":"false"}
  msgParams = {"text": "Other heat pump has finished. Resuming schedule."}
  rP_json = {'selection': rP_Selection, 'functions':[{'type':'resumeProgram','params':rP_Params},{"type":"sendMessage","params":msgParams}]}
  rP = post('https://api.ecobee.com/1/thermostat', headers=headers, json=rP_json)
  resultAPI = parseResponse(rP)
  return rP, resultAPI


#################################
# parse ecobee API response json
#################################

def parseResponse(item):
  import inspect
  from json import loads

  obj = loads(item.text)['status']
  statusCode = obj['code'] # 0 on success
  statusMessage = obj['message'] # "" on success
  statusCodeHTTP = item.status_code # 200 (possibly 2XX?) on success
  statusOK = item.ok # "True" on success

  caller = inspect.stack()[1].function
  parseObj = (caller, statusCode, statusMessage, statusCodeHTTP, statusOK)
  return parseObj


#################################
# convenience functions
#################################

def prowl(msg):
  import subprocess
  import inspect
  caller = inspect.stack()[1].function
  execList = ["./prowl.sh", str("\'ERROR: " + msg + "\'"), caller]
  output = subprocess.run(execList, capture_output = True)
  xmlobj = output.stdout.decode("utf-8")


def handleException(msg, logloc):
  from time import asctime
  import sys
  from local_functions import logfunc, prowl

  logfunc(logloc=logloc, line="ERROR: " + msg + ". Exiting.") # write to log file
  prowl(msg="Abnormal exit with '" + msg + "'") # send to prowl
  sys.exit(asctime() + ": ERROR: " + msg + ". Exiting.") # exit and raise descriptive exception
