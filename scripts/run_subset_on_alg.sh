#!/bin/bash

ALG="${1}"
MAX_INSTANCES_TO_RUN="${2}"
FILTER="${3}"
UPPAAL_FOLDER="${4}"
count=1

echo $ALG
echo $MAX_INSTANCES_TO_RUN
echo $FILTER
echo $UPPAAL_FOLDER

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ARTEFACT_DIR="$(dirname "$SCRIPT_DIR")"

declare -A algToNum
algToNum["concretemcr"]=0
algToNum["concretemcr_por"]=0
algToNum["lambdadeduction"]=5

declare -A algToGitBranchName
algToGitBranchName["concretemcr"]="roc"
algToGitBranchName["concretemcr_por"]="por"
algToGitBranchName["lambdadeduction"]="lambdadeduction"

echo Switching to git branch: ${algToGitBranchName["${ALG}"]}
cd $UPPAAL_FOLDER
git checkout ${algToGitBranchName["${ALG}"]}
bash ./server/scripts/cmakew.bash

for INSTANCE in $(ls -d $ARTEFACT_DIR/models/*${FILTER}*) ; do
  if [ $count -le $MAX_INSTANCES_TO_RUN ]
  then
    filename=$(basename ${INSTANCE})
    filename="${filename%.*}"
    ./server/build/linux64-release/build/bin/verifyta $INSTANCE --roc-alg=${algToNum["${ALG}"]} --ratio-type=1 >> $ARTEFACT_DIR/results/$ALG/$filename.txt
    echo Finished running $filename on $ALG
  fi
  (( count++ ))
done