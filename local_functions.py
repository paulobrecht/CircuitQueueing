# import os because a default function arg in some functions requires os.environ
import os

######################################################################################################################
#                                             C U R B    F U N C T I O N S                                           #
######################################################################################################################





def parseCurb(latest_json):
  """parse JSON data from Curb query

  Extended
  """

  import os

  CurbLocationID = os.environ["CURB_LOCATION_ID"]
  CurbAPIurl = os.environ["CURB_API_URL"]
  CurbAT = os.environ["CURB_ACCESS_TOKEN"]

  # outer dict
  stuff_keys = ["timestamp", "consumption", "production", "net"]

  try:
    stuff = {key: latest_json[key] for key in stuff_keys}

  except KeyError:
    circuits2 = {} # if what's pulled down doesn't have these keys, likely a Curb server issue
    pass

  else:
    circuits2 = {}
    for key in stuff_keys:
      circuits2[key] = stuff[key]

    # inner dict
    circuits = latest_json["circuits"]

    i=1
    for item in circuits:
      try:
        newk = item["id"]
      except KeyError:
        label = "Orphan " + str(i)
        circuits2[label] = item["w"]
        i += 1
      else:
        circuits2[item["label"]] = item["w"]

  return circuits2




def newCurbQuery(locationID=os.environ["CURB_LOCATION_ID"], apiURL=os.environ["CURB_API_URL"], AT=os.environ["CURB_ACCESS_TOKEN"]):
  """HTTP GET request to Curb server, which is parsed to flatten the JSON structure

  Extended
  """

  import os, requests
  from requests import exceptions
  from time import mktime, localtime
  from json import loads, dumps

  logloc = os.environ['CURB_LOCAL_LOG_LOC']

  # get latest usage data using daily token, then parse
  now = int(mktime(localtime()))
  try:
    latest = requests.get(apiURL + locationID, headers = {'authorization': 'Bearer ' + AT})
    latest.raise_for_status()
  except requests.exceptions.RequestException as err:
    handleException(msg="Error fetching Curb consumption data: " + err.response.text, logloc=logloc)
#    handleException(msg="Error fetching Curb consumption data: " + err.__str__(), logloc=logloc)

  latest_json = loads(latest.text)
  parsed = parseCurb(latest_json)

  # compute data_lag and add it to output
  parsed['data_lag'] = now - parsed['timestamp']

  return parsed



def curbUsage(cons):
  """Extract and calculate the device usage for the devices of interest

  Extended
  """

  from time import strftime, localtime

  consTime = strftime("%H:%M:%S", localtime(cons["timestamp"]))
  cons_keys = ["Heat Pump North", "Heat Pump South", "Water Heater North", "Water Heater South", \
               "Pool Pump 1", "Pool Pump 2", "Sub Panel 1", "Sub Panel 2", "Dryer 1", "Dryer 2"]

  # hogs does not include HPS, since that's the one we might be odeciding whether to override
  # also does not include water heaters since they defer to heat pumps
  # does not include dryer because that's a hard override of its own
  hogs = cons_keys[:1] + cons_keys[4:8]

  cons2 = {key: cons[key] for key in cons_keys}
  HPN, HPS, WHN, WHS, PP1, PP2, SUB1, SUB2, DRY1, DRY2 = cons2.values()

  SUB = SUB1 + SUB2
  DRY = DRY1 + DRY2
  PP = PP1 + PP2
  totalHogConsumption = sum([cons[x] for x in hogs])

  return (WHS, WHN, DRY, HPS, HPN, SUB, PP, totalHogConsumption)




######################################################################################################################
#                                         E C O B E E    F U N C T I O N S                                           #
######################################################################################################################




def getEcobeePin(key=os.environ['ECOBEE_API_KEY'], headers={'content-type': 'application/json', 'charset': 'UTF-8'}):
  """Get ecobee pin

  Sample call:
  jpin = getEcobeePin()
  ECOBEE_PIN, ECOBEE_PIN_CODE, ECOBEE_PIN_INTERVAL, ECOBEE_PIN_EXPIRY, ECOBEE_PIN_SCOPE = jpin.values()

  Extended
  """

  from json import loads
  from requests import get

  payload = {"response_type": "ecobeePin", "client_id": key, "scope": "smartWrite"}
  pin = get("https://api.ecobee.com/authorize", params=payload, headers=headers)
  jpin = loads(pin.text)
  return jpin




def getEcobeeAuthToken(pin, key=os.environ['ECOBEE_API_KEY'], headers={'content-type': 'application/json', 'charset': 'UTF-8'}):
  """Get ecobee auth token (using pin)

  Sample call:
  jkey = getEcobeeAuthToken(pin=ECOBEE_PIN, key=os.environ['ECOBEE_API_KEY'])
  ECOBEE_TOKEN, ECOBEE_TOKEN_TYPE, ECOBEE_TOKEN_EXPIRY, ECOBEE_SCOPE2, ECOBEE_REFRESH_TOKEN = jkey.values()

  First: User must manually logging into Ecobee website and authorizing the app using the PIN generated by getEcobeePin()

  Extended
  """

  from json import loads
  from requests import post
  from local_functions import logFunc

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
    logFunc(logloc=logloc, line=str("ERROR: Problem with removal of previous ecobee refresh token file. Trying to continue..."))

  try:
    ECOBEE_REFRESH_TOKEN = jkey['refresh_token']
    outfile = open(outloc, "w")
    outfile.write(ECOBEE_REFRESH_TOKEN)
    outfile.close()
  except Exception:
    logFunc(logloc=logloc, line=str("ERROR: Could not replace ecobee refresh token."))
    raise SystemExit(str("ERROR: Could not replace ecobee refresh token."))
  else:
    logFunc(logloc=logloc, line="getEcobeeAuthToken() refreshed ecobee refresh token.")

  return jkey




def refreshEcobeeAuthToken(refresh_token, key=os.environ['ECOBEE_API_KEY'], headers={'content-type': 'application/json', 'charset': 'UTF-8'}):
  """Refresh ecobee auth token (using refresh token)

  Sample call:
  jkey = refreshEcobeeAuthToken(refresh_token=os.environ['ECOBEE_REFRESH_TOKEN'])
  ECOBEE_TOKEN, ECOBEE_TOKEN_TYPE, ECOBEE_REFRESH_TOKEN, ECOBEE_TOKEN_EXPIRY, ECOBEE_SCOPE2 = jkey.values()

  Extended
  """

  from requests import post
  from json import loads

  payload = {"grant_type": "refresh_token", "refresh_token": refresh_token, "client_id": key}
  response = post("https://api.ecobee.com/token", params=payload, headers=headers)
  jkey = loads(response.text)
  return jkey





def queryEcobee(auth_token, includeSettings=True, includeEvents=False, headers={'content-type': 'application/json', 'charset': 'UTF-8'}):
  """ecobee /thermostat query

  Extended
  """

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




def postHold(auth_token, thermostatTime, heatRangeLow, coolRangeHigh, holdInterval=330, headers={'content-type': 'application/json', 'charset': 'UTF-8'}):
  """HTTP POST request to set a hold on the thermostat

  Extended
  """

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
  setHoldJSON = {'selection': setHoldSelection, 'functions':[{'type':'setHold', 'params':setHoldParams}]}

  setHold = post('https://api.ecobee.com/1/thermostat', headers=headers, json=setHoldJSON)
  resultAPI = parseEcobeeResponse(setHold)
  return setHold, endEpoch, resultAPI




def resumeProgram(auth_token, headers={'content-type': 'application/json', 'charset': 'UTF-8'}):
  """ecobee resume program (end hold)

  Extended
  """

  from requests import post

  tokenstr = "Bearer " + auth_token
  headers.update(Authorization = tokenstr)

  rP_Selection = {'selectionType':'registered','selectionMatch':''}
  rP_Params = {"resumeAll":"false"}
  rP_json = {'selection': rP_Selection, 'functions':[{'type':'resumeProgram','params':rP_Params}]}
  rP = post('https://api.ecobee.com/1/thermostat', headers=headers, json=rP_json)
  resultAPI = parseEcobeeResponse(rP)
  return rP, resultAPI




def parseEcobeeResponse(item):
  """parse ecobee API response json

  Extended
  """

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




######################################################################################################################
#                                   G E N E R A L    U T I L I T Y    F U N C T I O N S                              #
######################################################################################################################




def logFunc(logloc, line, now = None):
  """Write line to log file, default with timestamp

  Extended
  """

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



def getCaller():
  """Get name of script that called this function

  Extended
  """

  import inspect

  caller = ""
  func = ""

  def recurse(limit):
    local_variable = '.' * limit
    if limit <= 0:
        for frame, filename, line_num, func, source_code, source_index in inspect.stack():
            caller = filename.strip(os.environ['CURB_DIR'])
            func = source_code[source_index].strip()
        return caller, func
    caller, func = recurse(limit - 1)
    return caller, func

  caller, func = recurse(8)
# caller = caller + " (" + func + ")"
  return caller



def prowl(msg, short = "newshort"):
  """Send a prowl notification using prowl API

  Extended
  """

  import subprocess
  import inspect
  import string

  caller = getCaller()
  execList = [os.environ['CURB_DIR'] + "prowl.sh", str("\'" + msg + "\'"), caller, short]
  output = subprocess.run(execList, capture_output = True)
  xmlobj = output.stdout.decode("utf-8")
  return xmlobj



def handleException(inmsg, logloc, errorcode = 0, short = "newshort"):
  """Generic exception handler (logs error, sends a prowl notification, calls sys.exit())

  Extended
  """

  import sys
  from local_functions import logFunc, prowl

  if logloc != "":
    logFunc(logloc=logloc, line="ERROR: " + inmsg + ". Exiting.") # write to log file
  prowl(msg="ERROR: Abnormal exit with \'" + inmsg + "\'", short=short) # send to prowl
  sys.exit(errorcode)




def readConsumptionJSON(jsonloc):
  """Read the JSON file generated by fetchCurbData.py

  Extended
  """

  from json import loads

  with open(jsonloc) as file:
    for line in file:
      pass
    cons = loads(line)
  return cons




def averageProduction(jsonloc, duration = 5):
  """Read the JSON file generated by fetchCurbData.py to get average production

  Extended
  """

  from json import loads

  prodOverTime = {}
  with open(jsonloc) as file:
    for line in file:
      cons = loads(line)
      try:
        newkey = cons['timestamp']
        newprod = cons['production']
        prodOverTime[newkey] = newprod
      except KeyError:
        pass

  # sort dictionary by timestamp
  timestamps = list(prodOverTime.keys())
  timestamps.sort()
  prodOverTime = {i: prodOverTime[i] for i in timestamps}

  # get most recent X (default 5) production values (10 minutes)
  dictLength = len(prodOverTime)
  prodOverTimeList = list(prodOverTime.items())
  lastX = prodOverTimeList[dictLength-duration:]

  summed = 0
  for tup in lastX:
    summed += tup[1]
  avgProd = summed/duration

  return(avgProd)




def isOn(device_name, device_usage):
  """Define whether a device is running or not

  Extended
  """

  thresh = {"HPN": 2800, "HPS": 300, "DRY": 350, "SUB": 4000, "WHN": 500, "WHS": 500}
  status = int(device_usage > thresh[device_name])
  return status




def l2s(se):
  """Convience function to change [0, 1] to "OFF->ON"

  Extended
  """

  import local_functions as LF

  initial = LF.gpioMaps()[1][se[0]]
  end = LF.gpioMaps()[1][se[1]]

  return str(initial) + "->" + str(end)




######################################################################################################################
#                                             G P I O    F U N C T I O N S                                           #
######################################################################################################################




def gpioMaps():
  """mappings for GPIO stuff

  Extended
  """

  map1 = {"WH_north":11, "WH_south":13}
  map2 = {0:"OFF", 1:"ON"}
  return [map1, map2]




def gpioSetup(gpio_map = gpioMaps()[0]):
  """GPIO setup

  Extended
  """

  import RPi.GPIO as gpio

  gpio.setmode(gpio.BOARD)
  gpio.setwarnings(False)
  for x in [gpio_map[x] for x in gpio_map]:
    gpio.setup(x, gpio.OUT)




def gpioCheckStatus(device_list, gpio_map = gpioMaps()[0]):
  """Check GPIO status

  Extended
  """

  import RPi.GPIO as gpio
  gpioSetup()

  if isinstance(device_list, list):
    pass
  else:
    device_list = [device_list]

  status=[]
  for item in device_list:
    status.append(gpio.input(gpio_map[item]))

  # output device/status dict
  my_dict = {k:v for k,v in zip(device_list, status)}

  return my_dict




def gpioSetStatus(status_dict, gpio_map = gpioMaps()[0]):
  """Set GPIO status

  Extended
  """

  import RPi.GPIO as gpio

  for key in status_dict.keys():
    gpio.output(gpio_map[key], status_dict[key])





######################################################################################################################
#                                    C O N S U M P T I O N    F U N C T I O N S                                      #
######################################################################################################################

def readDryerHistory(jsonloc):
  """Read the JSON file generated by fetchCurbData.py to get average production

  Extended
  """
  from json import loads

  consOverTime = {}

  with open(jsonloc) as file:
    for line in file:
      cons = loads(line)
      try:
        newkey = cons['timestamp']
        newcons = cons['Dryer 1'] + cons['Dryer 2']
        consOverTime[newkey] = newcons
      except KeyError:
        pass

  # sort dictionary by timestamp
  timestamps = list(consOverTime.keys())
  timestamps.sort()
  consOverTime = {i: consOverTime[i] for i in timestamps}
  
  return(consOverTime, timestamps)



def readDeviceHistory(jsonloc, deviceName):
  """Read the JSON file generated by fetchCurbData.py to get average production

  Extended
  """
  from json import loads

  consOverTime = {}

  with open(jsonloc) as file:
    for line in file:
      cons = loads(line)
      try:
        newkey = cons['timestamp']
        newcons = cons[deviceName]
        consOverTime[newkey] = newcons
      except KeyError:
        pass

  # sort dictionary by timestamp
  timestamps = list(consOverTime.keys())
  timestamps.sort()
  consOverTime = {i: consOverTime[i] for i in timestamps}
  
  return(consOverTime, timestamps)



def calcAvgCons(deviceName, duration = 60):
  """Read the JSON file generated by fetchCurbData.py to get average production

  Extended
  """

  consOverTime, timestamps = readDeviceHistory(deviceName = deviceName)


  # get most recent X (default 5) production values (10 minutes)
  dictLength = len(consOverTime)
  consOverTimeList = list(consOverTime.items())
  lastX = consOverTimeList[dictLength-duration:]

  summed = 0
  for tup in lastX:
    summed += tup[1]
  avgCons = summed/duration

  return(avgCons)


def firstOnDryerTime(jsonloc):
  """Read the JSON file generated by fetchCurbData.py to get average production

  Extended
  """

  from datetime import datetime
  import os

  consOverTime, timestamps = readDryerHistory(jsonloc)

  # if device is on right now, see how long it has been on
  lastTimeStamp = timestamps[len(timestamps)-1]
  if consOverTime[lastTimeStamp] > 50: # only run this logic if device is on now
    reversetimestamps = timestamps.copy()
    reversetimestamps.reverse()
    i = lastTimeStamp
    j = 0
    while consOverTime[i] > 50: # will also be true by definition
      firston = i
      j += 1
      i = reversetimestamps[j]
    else:
      firstonHR = datetime.fromtimestamp(firston).strftime("%-I:%M %p")

    return(firstonHR, j)
  else:
    return(False, False)
