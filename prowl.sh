#!/bin/bash

. $HOME/CurbAPI_profile

# dt1=`date +"%D %H:%M:%S"` # Prowl provides, this adds nothing

apiurl="https://api.prowlapp.com/publicapi/add"
apikey=${PROWL_API_KEY}

description="$1"
application="$2"
event="$3"

curl $apiurl -F apikey=$apikey -F priority=0 -F application="${application}" -F event="${event}" -F description="${description}"
