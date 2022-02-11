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
for i in {1..2};
do
  echo $(eval mv \${fn$i} \${arch_fn$i})
done

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

# compress yesterday's archived files
for i in {1..2};
do
  echo $(eval gzip \${arch_fn$i})
done

# copy crontab to CurbAPI/crontab.txt for backup/version control
# but omit headers, but only when it changes
main="${rootdir}/crontab.txt"
copy="${rootdir}/old_crontabs/crontab" # no file extension

echo "$(crontab -l | grep -v ^\#)" > tmp
change=$(diff tmp $main | wc -l)
if [[ $change != 0 ]]; then
  mv $main ${copy}_${dt1}.txt
  gzip ${copy}_${dt1}.txt
  mv tmp $main
else
  rm -f tmp
fi
