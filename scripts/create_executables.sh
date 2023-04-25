#!/bin/bash

UPPAAL_FOLDER="$1"
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ARTEFACT_DIR="$(dirname "$SCRIPT_DIR")"
EXECUTABLE_DIR="${ARTEFACT_DIR}/executables"

mkdir -p $EXECUTABLE_DIR

declare -A algToGitBranchName
algToGitBranchName["concretemcr"]="roc"
algToGitBranchName["concretemcr_por"]="por"
algToGitBranchName["lambdadeduction"]="lambdadeduction"
declare -A algToGitCommit
algToGitCommit["concretemcr"]="3356821"
algToGitCommit["concretemcr_por"]="b68ac8c"
algToGitCommit["lambdadeduction"]="c8bface"

declare -a ALGS_TO_RUN=("concretemcr" "lambdadeduction" "concretemcr_por")

if [ "$2" != "all" ]
then
  ALGS_TO_RUN=("${@:2}")
fi

for ALG in "${ALGS_TO_RUN[@]}"
do
  echo Switching to git branch: ${algToGitBranchName["${ALG}"]}
  cd $UPPAAL_FOLDER || exit
  git checkout ${algToGitBranchName["${ALG}"]}
  git checkout ${algToGitCommit["${ALG}"]}
  bash ./server/scripts/cmakew.bash

  mkdir -p "$EXECUTABLE_DIR/${algToGitBranchName["${ALG}"]}"

  cp -r -v "./server/build/linux64-release/build" "${EXECUTABLE_DIR}/${algToGitBranchName["${ALG}"]}/build"
done

