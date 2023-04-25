#!/bin/bash

#TODO: RatioType and MaxInstances

declare -a ALGS_TO_RUN=("concretemcr" "lambdadeduction" "concretemcr_por")

if (( $# < 5 ))
then
  echo Incorrect usage. Arguments are: FILTER EXECUTABLE_DIR TIMEOUT_IN_SECONDS MAX_INSTANCES_TO_RUN ALGORITHMS_TO_RUN
  echo Example: './run_experiments.sh "strandvejen" /home/slorup/Documents/git/uppaal_roc_artefact/executables 600 100 lambdadeduction concretemcr'
  echo Example: './run_experiments.sh "strandvejen" /home/slorup/Documents/git/uppaal_roc_artefact/executables 600 100 all'
  echo Algorithms: "${ALGS_TO_RUN[*]}"
fi

FILTER="$1"
EXECUTABLE_FOLDER="$2"
TIMEOUT_SECONDS="$3"
MAX_INSTANCES="$4"

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )


if [ "$5" != "all" ]
then
  ALGS_TO_RUN=("${@:5}")
fi

cd $SCRIPT_DIR || exit

for ALG in "${ALGS_TO_RUN[@]}"
do
  ./run_subset_on_alg.sh "$ALG" $TIMEOUT_SECONDS $MAX_INSTANCES "$FILTER" "$EXECUTABLE_FOLDER"
done
