#!/bin/bash

dt1=`date +"%D %H:%M:%S"`

desc=$1
apiurl="https://api.prowlapp.com/publicapi/add"
apikey="50af7aee921448533f1941ffbcac7271f28b675f"
prty=0
app="CurbAPI"
event="Curb API query returned an error at ${dt1}"

curl $apiurl -F apikey=$apikey -F priority=$prty -F application="$app" -F event="$event" -F description="$desc"
