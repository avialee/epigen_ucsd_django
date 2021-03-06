#!/bin/bash

SEQ=$1
TENX_DIR=$2
USER_EMAIL=$3
tsccaccount=$4

TENXFILE=${TENX_DIR}${SEQ}"/."${SEQ}".tsv"
TYPE2='10xATAC'
#only one job shuold be submitted with this
n_libs=$( wc -l $TENXFILE |  awk '{print $1}'  )

cmd1="qsub -k oe -t 0-$[n_libs-1] -v samples=${TENXFILE} -M $USER_EMAIL -q hotel -l walltime=24:00:00 \$(which run10xPipeline.pbs)"

echo "${cmd1}"
job1=$(ssh $tsccaccount $cmd1)
    
