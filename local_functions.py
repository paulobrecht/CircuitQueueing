# log function
def logfunc(logloc, line, time=""):
  log = open(logloc, "a")
  if time == "":
    log.write(line + "\n")
  else:
    log.write(time + ": " + line + "\n")
  log.close()

# Curb query function
def curbQuery(locationID, apiURL, AT):

  import json
  import requests
  import os

  # get latest usage data using daily token
  Lurl = apiURL + locationID
  bearer_string = 'Bearer ' + AT
  headers = {'authorization': bearer_string, 'Keep-Alive': 'timeout=110, max=10'}
  latest = requests.get(Lurl, headers=headers)
  latest.close()

  # parse latest usage data ("log" is defined in calling script)
  latest_json = json.loads(latest.text)
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
    usage_list = [WHS, WHN, DRY, HPS, HPN, SUB, PP]
    outval = [usage_list, latest_json]
  return outval
