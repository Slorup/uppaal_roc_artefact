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

  EXE_DIR="${EXECUTABLE_DIR}/${algToGitBranchName["${ALG}"]}"

  mkdir -p "$EXE_DIR"

  cp -v "./server/build/linux64-release/build/bin/verifyta" "$EXE_DIR"
  cp -v "./server/build/linux64-release/build/bin/libcrypto.so.1.1" "$EXE_DIR"
  cp -v "./server/build/linux64-release/build/bin/libglpk.so.40" "$EXE_DIR"
  cp -v "./server/build/linux64-release/build/bin/libprlearn.so" "$EXE_DIR"
  cp -v "./server/build/linux64-release/build/bin/libssl.so.1.1" "$EXE_DIR"
  cp -v "./server/build/linux64-release/build/bin/libstrategy.so" "$EXE_DIR"
  cp -v "./server/build/linux64-release/build/bin/lib/libc.so.6" "$EXE_DIR"
  cp -v "./server/build/linux64-release/build/bin/lib/libgcc_s.so.1" "$EXE_DIR"
  cp -v "./server/build/linux64-release/build/bin/lib/libm.so.6" "$EXE_DIR"
  cp -v "./server/build/linux64-release/build/bin/lib/libstdc++.so.6" "$EXE_DIR"
  cp -v "${SCRIPT_DIR}/run_verifyta.sh" "${EXE_DIR}"
done

