#!/bin/bash

#TODO: RatioType and MaxInstances

FILTER="$1"
UPPAAL_FOLDER="$2"
MAX_INSTANCES=300

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

declare -a ALGS_TO_RUN=("concretemcr" "lambdadeduction" "concretemcr_por")

if [ "$3" != "all" ]
then
  ALGS_TO_RUN=("${@:3}")
fi

cd $SCRIPT_DIR || exit

for ALG in "${ALGS_TO_RUN[@]}"
do
  ./run_subset_on_alg.sh "$ALG" $MAX_INSTANCES "$FILTER" "$UPPAAL_FOLDER"
done