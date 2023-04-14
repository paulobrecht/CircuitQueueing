#!/bin/bash

dt1=`date +'%Y-%m-%d' -d 'yesterday'` # YMD yesterday, for archive log file names
dt2=`date +'%H:%M:%S'` # HMS right now
dt3=`date +'%A, %B %e'` # For file headers

rootdir="$HOME/CurbAPI"
logdir="${rootdir}/logs"
fn1="${rootdir}/activity_log.txt"
fn2="${rootdir}/consumption_log.json"
arch_fn1="${logdir}/activity_log_${dt1}.txt"
arch_fn2="${logdir}/consumption_log_${dt1}.json"

[[ ! -d ${logdir} ]] && mkdir -p ${logdir}

# archive yesterday's files
mv ${fn1} ${arch_fn1}
gzip ${arch_fn1}
mv ${fn2} ${arch_fn2}
gzip ${arch_fn2}

# make new activity log file
touch ${fn1}
echo "- - - - - - - - - - - - - - - - - - - - - - - -"          >> ${fn1}
echo "Log File for ${dt3}"                                      >> ${fn1}
echo "- - - - - - - - - - - - - - - - - - - - - - - -"          >> ${fn1}
echo ""                                                         >> ${fn1}
echo "${dt2}: Archived yesterday's file, starting a fresh one." >> ${fn1}
echo ""                                                         >> ${fn1}

# make new consumption log file (no headers because that complicates parsing)
touch ${fn2}

# copy crontab to CurbAPI/crontab.txt (omit headers), but only when it changes
# also archive the old one for backup/version control
copy="${rootdir}/crontab_current.txt"
arch="${rootdir}/old_crontabs/crontab_${dt1}.txt"

if [[ -f $copy ]]; then # first make sure crontab_current.txt exists
  echo "$(crontab -l | grep -v ^\#)" > tmp # active crontab to tmp file
  change=$(diff tmp $copy | wc -l) # did it change?
  if [[ $change != 0 ]]; then # if it changed
    mv $copy $arch
    mv tmp $copy
    gzip $arch
    echo "${dt2}: Crontab changed. Updated crontab_current.txt. Archived the old." >> ${fn1}
  else # if no change, rm tmp and exit
    rm -f tmp
  fi
else # if crontab_current.txt doesn't exist, make it. But there's nothing to archive
  echo "$(crontab -l | grep -v ^\#)" > $copy # active crontab to tmp file
  echo "${dt2}: crontab_current.txt not found. Copied active crontab to that location." >> ${fn1}
fi
