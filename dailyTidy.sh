#!/bin/bash

dt1=`date +'%Y-%m-%d'` # YMD right now, for archive log file name
dt2=`date +'%H:%M:%S'` # HMS right now
dt3=$(date +'%A, %B %e' -d "+1 day") # tomnorrow for header

rootdir="$HOME/CurbAPI"
logdir="${rootdir}/logs"
fn1="${rootdir}/activity_log.txt"
fn2="${rootdir}/consumption_log.json"
arch_fn1="${logdir}/activity_log_${dt1}.txt"
arch_fn2="${logdir}/consumption_log_${dt1}.json"

[[ ! -d ${logdir} ]] && mkdir -p ${logdir}

# archive yesterday's files
mv ${fn1} ${arch_fn1}
mv ${fn2} ${arch_fn2}

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

# compress archives
gzip ${arch_fn1} ${arch_fn2}
