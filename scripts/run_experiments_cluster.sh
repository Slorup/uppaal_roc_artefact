#!/bin/bash
#SBATCH --time=1:00:00
#SBATCH --mail-user=nsjo18@student.aau.dk
#SBATCH --mail-type=FAIL
#SBATCH --partition=naples
#SBATCH --mem=8G
#SBATCH --cpus-per-task=1

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
count=0

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ARTEFACT_DIR="$(dirname "$SCRIPT_DIR")"

if [ "$5" != "all" ]
then
  ALGS_TO_RUN=("${@:5}")
fi

cd $SCRIPT_DIR || exit

for ALG in "${ALGS_TO_RUN[@]}" ; do
  count=0
  for INSTANCE in $ARTEFACT_DIR/models/*${FILTER}*.xml* ; do
    [[ -e "$INSTANCE" ]] || break
    if [ $count -le $MAX_INSTANCES ]
    then
      sbatch ./run_instance.sh "$ALG" $TIMEOUT_SECONDS "$INSTANCE" "$EXECUTABLE_FOLDER"
    fi
    (( count++ ))
  done
done
