#!/bin/bash
#SBATCH --partition=naples
#SBATCH --mem=10G
#SBATCH --cpus-per-task=1

declare -a ALGS_TO_RUN=("concretemcr" "lambdadeduction" "lambdadeduction_no_optimisations" "lambdadeduction_transformation_matrix" "lambdadeduction_prune_parent" "lambdadeduction_reuse_waiting" "lambdadeduction_full_no_reuse_waiting" "lambdadeduction_keep_parent")

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
KEY="$5"
count=1

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ARTEFACT_DIR="$(dirname "$SCRIPT_DIR")"

if [ "$6" != "all" ]
then
  ALGS_TO_RUN=("${@:6}")
fi

cd "$SCRIPT_DIR" || exit

for ALG in "${ALGS_TO_RUN[@]}" ; do
  count=1
  for INSTANCE in $ARTEFACT_DIR/models/benchmark/${FILTER}* ; do
    [[ -e "$INSTANCE" ]] || break
    if [ $count -le "$MAX_INSTANCES" ]
    then
      sbatch ./run_instance.sh "$ALG" "$TIMEOUT_SECONDS" "$INSTANCE" "$EXECUTABLE_FOLDER" "$ARTEFACT_DIR" "$KEY"
    fi
    (( count++ ))
  done
done
