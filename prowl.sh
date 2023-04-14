#!/bin/bash

dt1=`date +"%D %H:%M:%S"`

apiurl="https://api.prowlapp.com/publicapi/add"
apikey=${PROWL_API_KEY}
prty=0
event="${2} returned an error at ${dt1}"

curl $apiurl -F apikey=$apikey -F priority=$prty -F application="$2" -F event="$event" -F description="$1"
