#!/bin/bash

dt1=`date +'%Y-%m-%d' -d 'yesterday'` # YMD yesterday, for archive log file names
dt2=`date +'%H:%M:%S'` # HMS right now
dt3=`date +'%A, %B %e'` # For file headers

rootdir="$HOME/CurbAPI"
logdir="${rootdir}/logs"
fn1="${rootdir}/activity_log.txt"
fn2="${rootdir}/consumption_log.json"
fn3="${rootdir}/ecobee_activity_log.txt"
arch_fn1="${logdir}/activity_log_${dt1}.txt"
arch_fn2="${logdir}/consumption_log_${dt1}.json"
arch_fn3="${logdir}/ecobee_activity_log_${dt1}.txt"

[[ ! -d ${logdir} ]] && mkdir -p ${logdir}

# archive yesterday's files
for i in {1..3};
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

# make new ecobee activity log file
touch ${fn3}
echo "- - - - - - - - - - - - - - - - - - - - - - - -"          >> ${fn3}
echo "Ecobee Activity Log File for ${dt3}"                      >> ${fn3}
echo "- - - - - - - - - - - - - - - - - - - - - - - -"          >> ${fn3}
echo ""                                                         >> ${fn3}
echo "${dt2}: Archived yesterday's file, starting a fresh one." >> ${fn3}
echo ""                                                         >> ${fn3}

# compress archives
for i in {1..3};
do
  echo $(eval gzip \${arch_fn$i})
done
