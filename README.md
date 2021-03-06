# CircuitQueueing

A solar energy efficiency project using Curb home energy monitoring, a raspberry pi, the ecobee API, and some relays in the electrical panel. The project forces large household appliances into a priority hierarchy, forcing them to run one or two at a time, and preventing some from running at night and high rate electrical utility hours.

## The main idea:

### Overview

The complete list of devices that enter into this process are:

1. The kitchen subpanel, which contains the electric ovens, the electric range, fridge/freezer, microwave, dishwasher, etc.
2. The two water heaters
3. The two heat pumps; one is "smart," and one is dumb
4. The pool pump
5. The dryer

The relays are on the two water heaters and the pool pump. The ecobee API allows overriding one of the heat pumps. The kitchen, the "dumb" heat pump, and the dryer are all inputs; they can't be overridden.

## Overrides
+ Time of use override: In winter months, the local utility charges premium rates for consumption from 6 am to 9 am and from 6 pm to 9 pm. `FlipRelayWH.sh` cuts the power supply to the two water heaters and the pool pump during those hours. During summer months, crontab has to be updated to accommodate summer peak rate hours.
+ Late at night: from 11 pm to 5 am the water heaters are prevented from running.

### Water Heaters and Pool Pump

A Raspberry pi and solid state relays in the electrical panel can turn on or off the two water heaters and/or the pool pump by interrupting the current at the breaker. The python scripts for this logic are all executed by cron. Cron usually launches an associated .sh file, which in turn launches the .py script.

+ `crontab.txt`... a dump of the crontab, performed in `dailyTidy.sh`
+ `getAccessToken.py`... the Curb API access token has to be refreshed daily.
+ `fetchCurbData.py`... fetches circuit-level consumption data from the Curb API every minute and appends it to a local json file
+ `curbLogic.py`... the main logic for turning on and off the relays based on reading the latest row in the consumption json file
+ `local_functions.py`... various functions used by various scripts
+ `dailyTidy.sh`... zips and stores the activity log file and creates a new one every day at midnight
+ `flipRelayWH.sh`... Flips all the relays either ON or OFF with a command-line argument. Used here only with OFF to override all devices at peak rate times and overnight.
+ `prowl.sh`... used to fire a prowl alert under certain circumstances
+ `4shortcuts`... this houses scripts that I can fire from my phone using the iOS Shortcuts app to override the queueing jobs.

    The override script is executed once daily by cron as well. From 5 am to 6 am, all devices are allowed to run freely, to ensure that we have both hot water for showers and a warm house at 6 am to start the day.
    
+ `CurbAPI_profile` bash env variables to store values used by all the scripts. The true file is stored outside this directory because it contains secret keys, etc. This is a copy that anonymizes the sensitive values.

### Ecobee API

There's also a component that uses the ecobee API to put a temperature hold on one heat pump if certain conditions met. Both thermostats allow for multiple environment settings configurable by time of day, but there's no way for one thermostat to know that the other heat pump is currenly running. This process allows a hold to be placed on one heat pump for the duration that the other one is running. The script that controls that process is `ecobeeOverride.py`. 
