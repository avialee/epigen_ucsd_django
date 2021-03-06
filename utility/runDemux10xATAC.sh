#!/bin/bash

## cmd1: qsub job from tscc 
flowcell=$1; rundir=$2; useremail=$3; tsccaccount=$4; extraPars=${@:4:5};
if [ -z $extraPars ]
then
    cmd1="qsub -k oe  -M $useremail -v flowcell_id=$flowcell,run_dir=$rundir \$(which runDemux10xATAC.pbs)"
else
    cmd1="qsub -k oe  -M $useremail -v flowcell_id=$flowcell,run_dir=$rundir,extraPars=\"$extraPars\" \$(which runDemux10xATAC.pbs)"
fi

echo $cmd1
ssh $tsccaccount $cmd1


