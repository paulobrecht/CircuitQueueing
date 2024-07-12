#!/bin/bash

. $HOME/CurbAPI_profile

# date and script name
dt=$(date +'%H:%M:%S') # HMS right now
month=$(date +'%m')
monthW=$(date +'%b')
me=$(basename "$0")

# project directory and logfile
rootdir="${CURB_DIR}"
logfile="${CURB_LOCAL_LOG_LOC}"
always="${rootdir}/textfiles/ct_template_always.txt"
summer="${rootdir}/textfiles/ct_template_summer.txt"
winter="${rootdir}/textfiles/ct_template_winter.txt"

if [[ -f ${summer} ]] && [[ -f ${winter} ]] && [[ -f ${always} ]]; then
  if [[ "${month}" == "05" ]]; then
    cat ${always} ${summer} > tmpcron 
  elif [[ "${month}" == "10" ]]; then
    cat ${always} ${winter} > tmpcron 
  else
    echo "${dt}: ${me} script ran in ${monthW} but is only supposed to run in May and Oct. Exited without doing anything." >> $logfile
    ${rootdir}/prowl.sh "'Script ran in ${monthW} but is only supposed to run in May and Oct. Exited without doing anything.'" "${me}" "Crontab update ran in incorrect month" > /dev/null
    exit 9
  fi

  # copy assembled template file to crontab
 /usr/bin/crontab -u pi tmpcron
 rc=$?
  echo "${dt}: Crontab update for ${monthW} change in TEP peak hours ran with exit code ${rc}." >> $logfile
else
  echo "${dt}: Tried to update crontab to reflect ${monthW} change in TEP peak hours, but did not find template file(s)." >> $logfile # log error to log file
  ${rootdir}/prowl.sh "'Could not update crontab for TEP, did not find template file(s).'" "${me}" "Crontab template files missing" > /dev/null
fi

rm tmpcron
