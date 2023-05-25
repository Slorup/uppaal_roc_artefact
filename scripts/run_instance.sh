#!/bin/bash
#SBATCH --time=0:05:00
#SBATCH --error=/nfs/home/student.aau.dk/nsjo18/uppaal_roc_artefact/slurm-output/run-instance-%j.err
#SBATCH --output=/nfs/home/student.aau.dk/nsjo18/uppaal_roc_artefact/slurm-output/setup-venv-%j.out
#SBATCH --partition=naples
#SBATCH --mem=10G
#SBATCH --cpus-per-task=1

let "m=1000*1000*10"
ulimit -v $m

ALG="${1}"
TIME_LIMIT="${2}"
INSTANCE="${3}"
EXECUTABLE_DIR="${4}"
ARTEFACT_DIR="${5}"
KEY="${6}"

declare -A algToGitBranchName
algToGitBranchName["concretemcr"]="concretemcr"
algToGitBranchName["concretemcr_por"]="concretemcr_por"
algToGitBranchName["lambdadeduction"]="lambdadeduction"
algToGitBranchName["lambdadeduction_no_optimisations"]="lambdadeduction"
algToGitBranchName["lambdadeduction_transformation_matrix"]="lambdadeduction"
algToGitBranchName["lambdadeduction_prune_parent"]="lambdadeduction"
algToGitBranchName["lambdadeduction_reuse_waiting"]="lambdadeduction"
algToGitBranchName["bdd"]="bdd"

declare -A algToVerifytaOptions
algToVerifytaOptions["concretemcr"]="--roc-alg=0 --ratio-type=1"
algToVerifytaOptions["concretemcr_por"]="--roc-alg=0 --ratio-type=1"
algToVerifytaOptions["lambdadeduction"]="--roc-alg=5 --ratio-type=1"
algToVerifytaOptions["lambdadeduction_no_optimisations"]="--roc-alg=5 --ratio-type=1 --no-transformation-matrix --clean-waiting --no-parent-pruning"
algToVerifytaOptions["lambdadeduction_transformation_matrix"]="--roc-alg=5 --ratio-type=1 --clean-waiting --no-parent-pruning"
algToVerifytaOptions["lambdadeduction_prune_parent"]="--roc-alg=5 --ratio-type=1 --clean-waiting --no-transformation-matrix"
algToVerifytaOptions["lambdadeduction_reuse_waiting"]="--roc-alg=5 --ratio-type=1 --no-parent-pruning --no-transformation-matrix"
algToVerifytaOptions["bdd"]="--roc-alg=5 --ratio-type=1"

cd "$ARTEFACT_DIR" || exit
mkdir -p results/"$ALG"

filename=$(basename "${INSTANCE}")
filename="${filename%.*}"
RESULT_FILE="$ARTEFACT_DIR/results/${ALG}/$filename.txt"
[ -f "$RESULT_FILE" ] && rm "$RESULT_FILE"
echo Running "$filename" on "$ALG" ..
/usr/bin/time -f "@@@%e,%M@@@" timeout "$TIME_LIMIT" "${EXECUTABLE_DIR}/${algToGitBranchName["${ALG}"]}/verifyta" "--key=$KEY" "$INSTANCE" ${algToVerifytaOptions["${ALG}"]} &> "$RESULT_FILE"
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
