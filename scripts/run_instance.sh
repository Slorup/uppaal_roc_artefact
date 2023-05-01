#!/bin/bash
#SBATCH --time=1:00:00
#SBATCH --mail-user=nsjo18@student.aau.dk
#SBATCH --mail-type=FAIL
#SBATCH --error=/nfs/home/student.aau.dk/nsjo18/slurm-output/run-tool-%j.err
#SBATCH --partition=naples
#SBATCH --mem=8G
#SBATCH --cpus-per-task=1

let "m=1024*1024*8"
ulimit -v $m

ALG="${1}"
TIME_LIMIT="${2}"
INSTANCE="${3}"
EXECUTABLE_DIR="${4}"
ARTEFACT_DIR="${5}"

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
