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

# make new consumption log file
touch ${fn2}
echo "- - - - - - - - - - - - - - - - - - - - - - - -"          >> ${fn2}
echo "Consumption Log File for ${dt3}"                          >> ${fn2}
echo "- - - - - - - - - - - - - - - - - - - - - - - -"          >> ${fn2}
echo ""                                                         >> ${fn2}
echo "${dt2}: Archived yesterday's file, starting a fresh one." >> ${fn2}
echo ""                                                         >> ${fn2}

# copy crontab to CurbAPI/crontab.txt (omit headers)
# for backup/version control, but only when it changes
main="${rootdir}/crontab.txt"
copy="${rootdir}/old_crontabs/crontab_${dt1}.txt" # no file extension

echo "$(crontab -l | grep -v ^\#)" > tmp
change=$(diff tmp $main | wc -l)
if [[ $change != 0 ]]; then
  mv $main $copy
  gzip $copy
  mv tmp $main
else
  rm -f tmp
fi
