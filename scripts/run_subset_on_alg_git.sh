#!/bin/bash

ALG="${1}"
MAX_INSTANCES_TO_RUN="${2}"
FILTER="${3}"
UPPAAL_FOLDER="${4}"
count=1

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ARTEFACT_DIR="$(dirname "$SCRIPT_DIR")"

TIME_LIMIT=600

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

declare -A algToGitCommit
algToGitCommit["concretemcr"]="c59f3eb"
algToGitCommit["concretemcr_por"]="6859b6e"
algToGitCommit["lambdadeduction"]="a9d1078"
algToGitCommit["bdd"]="529b66a"

cd $ARTEFACT_DIR || exit
mkdir -p results/$ALG

echo Switching to git branch: ${algToGitBranchName["${ALG}"]}
cd $UPPAAL_FOLDER || exit
git checkout ${algToGitBranchName["${ALG}"]}
git checkout ${algToGitCommit["${ALG}"]}
bash ./server/scripts/cmakew.bash

for INSTANCE in $ARTEFACT_DIR/models/*${FILTER}*.xml* ; do
  [[ -e "$INSTANCE" ]] || break
  if [ $count -le $MAX_INSTANCES_TO_RUN ]
  then
    filename=$(basename ${INSTANCE})
    filename="${filename%.*}"
    echo Running $filename on $ALG ..
    timeout $TIME_LIMIT ./server/build/linux64-release/build/bin/verifyta $INSTANCE --roc-alg=${algToNum["${ALG}"]} --ratio-type=1 >> $ARTEFACT_DIR/results/$ALG/$filename.txt
    exit_status=$?
    if [[ $exit_status -eq 124 ]]; then
    	echo "Timed Out" >> $ARTEFACT_DIR/results/$ALG/$filename.txt
    	echo Timed out running $filename on $ALG 
    else
      echo Finished running $filename on $ALG
    fi
  fi
  (( count++ ))
done
