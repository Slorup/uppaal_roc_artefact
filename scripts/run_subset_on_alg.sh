#!/bin/bash

let "m=1024*1024*8"
ulimit -v $m

ALG="${1}"
TIME_LIMIT="${2}"
MAX_INSTANCES_TO_RUN="${3}"
FILTER="${4}"
EXECUTABLE_DIR="${5}"
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ARTEFACT_DIR="$(dirname "$SCRIPT_DIR")"
count=1

declare -A algToNum
algToNum["concretemcr"]=0
algToNum["concretemcr_por"]=0
algToNum["lambdadeduction"]=5
algToNum["bdd"]=5

declare -A algToGitBranchName
algToGitBranchName["concretemcr"]="roc"
algToGitBranchName["concretemcr_por"]="por"
algToGitBranchName["lambdadeduction"]="lambdadeduction"
algToGitBranchName["bdd"]="bdd"

cd $ARTEFACT_DIR || exit
mkdir -p results/$ALG

for INSTANCE in $ARTEFACT_DIR/models/*${FILTER}*.xml* ; do
  [[ -e "$INSTANCE" ]] || break
  if [ $count -le $MAX_INSTANCES_TO_RUN ]
  then
    filename=$(basename ${INSTANCE})
    filename="${filename%.*}"
    echo Running $filename on $ALG ..
    timeout $TIME_LIMIT "${EXECUTABLE_DIR}/${algToGitBranchName["${ALG}"]}/verifyta" $INSTANCE --roc-alg=${algToNum["${ALG}"]} --ratio-type=1 >> $ARTEFACT_DIR/results/${algToGitBranchName["${ALG}"]}/$filename.txt
    exit_status=$?
    if [[ $exit_status -eq 124 ]]; then
    	echo "Timed Out" >> $ARTEFACT_DIR/results/$ALG/$filename.txt
    	echo Timed out running $filename on $ALG
    elif [[ $exit_status -eq 137 ]] || [[ $exit_status -eq 1 ]]; then
      echo "Out of memory" >> $ARTEFACT_DIR/results/$ALG/$filename.txt
      echo Ran out of memory running $filename on $ALG
    else
      echo Finished running $filename on $ALG
    fi
  fi
  (( count++ ))
done
