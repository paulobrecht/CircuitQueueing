# CircuitQueueing

A solar energy efficiency project using Curb home energy monitoring, a raspberry pi, the ecobee API, and some relays in the electrical panel. The project forces large household appliances into a priority hierarchy, forcing them to run one or two at a time, and preventing some from running at night and high rate electrical utility hours.

## The main idea is this:

A Raspberry pi and solid state relays in the electrical panel can turn on or off the two water heaters and/or the pool pump by interrupting the current at the breaker. The python scripts for this logic are all executed by cron. Cron actually launches an associated .sh file, which in turn launches the .py script.

+ `crontab.txt`... a dump of the crontab, performed in `dailyTidy.sh`
+ `getAccessToken.py`... the Curb API access token has to be refreshed daily.
+ `fetchCurbData.py`... fetches circuit-level consumption data from the Curb API every minute and appends it to a local json file
+ `curbLogic.py`... the main logic for turning on and off the relays based on reading the latest row in the consumption json file
+ `local_functions.py`... various functions used by various scripts
+ `dailyTidy.sh`... zips and stores the activity log file and creates a new one every day at midnight
+ `flipRelayWH.sh`... Flips all the relays either ON or OFF with a command-line argument. Used here only with OFF to override all devices at peak rate times and overnight.
+ `prowl.sh`... used to fire a prowl alert under certain circumstances
+ `4shortcuts`... this houses scripts that I can fire from my phone using the iOS Shortcuts app to override the queueing jobs.
+ `CurbAPI_profile` bash env variables to store values used by all the scripts. The true file is stored outside this directory because it contains secret keys, etc. This is a copy that anonymizes the sensitive values.

There's also a component that uses the ecobee API to put a temperature hold on one heat pump if certain conditions met. The script that controls that process is `ecobeeOverride.py`.

The complete list of devices that enter into this process are:

1. The kitchen subpanel, which contains the electric ovens, the electric range, fridge/freezer, microwave, dishwasher, etc.
2. The two water heaters
3. The two heat pumps; one is "smart," and one is dumb
4. The pool pump
5. The dryer

The relays are on the two water heaters and the pool pump. The ecobee API allows overriding one of the heat pumps. The kitchen, the "dumb" heat pump, and the dryer are all inputs; they can't be overridden.
