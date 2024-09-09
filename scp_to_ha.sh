#!/usr/bin/bash

/usr/bin/scp -pq /home/pi/CurbAPI/textfiles/consumption_log.json root@homeassistant.local:/config/files/consumption_log.json
rc=$?
