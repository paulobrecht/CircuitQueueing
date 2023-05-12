def myfn(x):
  parsed = x.split(",")
  if parsed[2] == '':
    return None
  else:
    return parsed[2]


def getOutsideTemp(auth_token, includeSettings=True, includeEvents=False, tstat_id="522687539900", headers={'content-type': 'application/json', 'charset': 'UTF-8'}):
  """ecobee /runtimeReport query

  Extended
  """

  from json import loads
  from requests import get
  from time import strftime, localtime

  # strings
  sm = "selectionMatch: " + tstat_id
  today = strftime('%Y-%m-%d', localtime())
  tokenstr = "Bearer " + auth_token

  # auth header
  headers.update(Authorization = tokenstr)

  # get outdoor temp
  payload = {'format': 'json', 'body': '{"startDate": ' + today + ', "endDate": ' + today + ', "columns": "outdoorTemp", "selection": {"selectionType": "thermostats", ' + sm + '}}'}
  tstat = get('https://api.ecobee.com/1/runtimeReport', headers=headers, params=payload)
  status = tstat.status_code

  if status != 200:
    rtnVal = "Non-200"
  else:
    tstat = loads(tstat.text)
    times = tstat['reportList'][0]['rowList']
    tempList = [myfn(x) for x in times]
    tempList2 = list(filter(lambda item: item is not None, tempList))
    lastTemp = float(tempList2[len(tempList2)-1])

    rtnVal = lastTemp

  return rtnVal