#!/bin/bash

let "m=1024*1024*5"
ulimit -v $m

ALG="${1}"
TIME_LIMIT="${2}"
MAX_INSTANCES_TO_RUN="${3}"
FILTER="${4}"
EXECUTABLE_DIR="${5}"
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ARTEFACT_DIR="$(dirname "$SCRIPT_DIR")"
count=1

declare -A algToGitBranchName
algToGitBranchName["concretemcr"]="concretemcr"
algToGitBranchName["concretemcr_por"]="concretemcr_por"
algToGitBranchName["lambdadeduction"]="lambdadeduction"
algToGitBranchName["lambdadeduction_full_no_reuse_waiting"]="lambdadeduction"
algToGitBranchName["lambdadeduction_no_optimisations"]="lambdadeduction"
algToGitBranchName["lambdadeduction_transformation_matrix"]="lambdadeduction"
algToGitBranchName["lambdadeduction_prune_parent"]="lambdadeduction"
algToGitBranchName["lambdadeduction_reuse_waiting"]="lambdadeduction"
algToGitBranchName["lambdadeduction_full_reset_cost"]="lambdadeduction"
algToGitBranchName["lambdadeduction_keep_parent"]="lambdadeduction"
algToGitBranchName["bdd"]="bdd"

declare -A algToVerifytaOptions
algToVerifytaOptions["concretemcr"]="--roc-alg=0 --ratio-type=1"
algToVerifytaOptions["concretemcr_por"]="--roc-alg=0 --ratio-type=1"
algToVerifytaOptions["lambdadeduction"]="--roc-alg=5 --ratio-type=1"
algToVerifytaOptions["lambdadeduction_full_no_reuse_waiting"]="--roc-alg=5 --ratio-type=1 --clean-waiting"
algToVerifytaOptions["lambdadeduction_no_optimisations"]="--roc-alg=5 --ratio-type=1 --no-transformation-matrix --clean-waiting --no-parent-pruning"
algToVerifytaOptions["lambdadeduction_transformation_matrix"]="--roc-alg=5 --ratio-type=1 --clean-waiting --no-parent-pruning"
algToVerifytaOptions["lambdadeduction_prune_parent"]="--roc-alg=5 --ratio-type=1 --clean-waiting --no-transformation-matrix"
algToVerifytaOptions["lambdadeduction_reuse_waiting"]="--roc-alg=5 --ratio-type=1 --no-parent-pruning --no-transformation-matrix"
algToVerifytaOptions["lambdadeduction_full_reset_cost"]="--roc-alg=5 --ratio-type=1 --reset-cost-on-lambda-improvement"
algToVerifytaOptions["lambdadeduction_keep_parent"]="--roc-alg=5 --ratio-type=1 --keep-parent"
algToVerifytaOptions["bdd"]="--roc-alg=5 --ratio-type=1"

cd "$ARTEFACT_DIR" || exit
mkdir -p results/"${ALG}"

for INSTANCE in "$ARTEFACT_DIR"/models/benchmark/*${FILTER}*.xml* ; do
  [[ -e "$INSTANCE" ]] || break
  if [ $count -le "$MAX_INSTANCES_TO_RUN" ]
  then
    filename=$(basename "${INSTANCE}")
    filename="${filename%.*}"
    RESULT_FILE="$ARTEFACT_DIR/results/${ALG}/$filename.txt"
    [ -f "$RESULT_FILE" ] && rm "$RESULT_FILE"
    echo Running "$filename" on "$ALG" ..
    /usr/bin/time -f "@@@%e,%M@@@" timeout "$TIME_LIMIT" "${EXECUTABLE_DIR}/${algToGitBranchName["${ALG}"]}/verifyta" "$INSTANCE" ${algToVerifytaOptions["${ALG}"]} &> "$RESULT_FILE"
    exit_status=$?
    if [[ $exit_status -eq 124 ]]; then
    	echo "Timed Out" >> "$RESULT_FILE"
    	echo Timed out running "$filename" on "$ALG"
    elif [[ $exit_status -eq 137 ]]; then
      echo "Out of memory" >> "$RESULT_FILE"
      echo Ran out of memory running "$filename" on "$ALG"
    elif [[ $exit_status -eq 1 ]]; then
      echo "Maybe ran out of memory" >> "$RESULT_FILE"
      echo Maybe ran out of memory running "$filename" on "$ALG"
    else
      echo Finished running "$filename" on "$ALG"
    fi
  fi
  (( count++ ))
done