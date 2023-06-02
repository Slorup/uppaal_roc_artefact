#!/bin/bash

UPPAAL_FOLDER="$1"
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ARTEFACT_DIR="$(dirname "$SCRIPT_DIR")"
EXECUTABLE_DIR="${ARTEFACT_DIR}/executables"

mkdir -p $EXECUTABLE_DIR

declare -A algToGitCommit
algToGitCommit["concretemcr"]="0c28d89"
algToGitCommit["concretemcr_por"]="25f60b7"
algToGitCommit["lambdadeduction"]="341888d"
algToGitCommit["bdd"]="529b66a"

declare -a ALGS_TO_RUN=("concretemcr" "lambdadeduction" "concretemcr_por" "bdd")

if [ "$2" != "all" ]
then
  ALGS_TO_RUN=("${@:2}")
fi

cd "$UPPAAL_FOLDER" || exit
PREVIOUS_BRANCH=$(git branch | sed -n -e 's/^\* \(.*\)/\1/p')

for ALG in "${ALGS_TO_RUN[@]}"
do
  echo Switching to git branch: "$ALG"
  cd "$UPPAAL_FOLDER" || exit
  git checkout ${algToGitCommit["${ALG}"]}
  bash ./server/scripts/cmakew.bash

  EXE_DIR="${EXECUTABLE_DIR}/$ALG"

  mkdir -p "$EXE_DIR"

  #cp -r -v "./server/build/linux64-release/build/bin" "$EXE_DIR"

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

  [ -f "./server/build/linux64-release/build/bin/libcudd-3.0.0.so.0" ] && cp -v "./server/build/linux64-release/build/bin/libcudd-3.0.0.so.0" "$EXE_DIR"

  mv "$EXE_DIR"/verifyta "$EXE_DIR"/verifyta.bin

  cp -v "${SCRIPT_DIR}/verifyta" "${EXE_DIR}"
  cp -v "${SCRIPT_DIR}/ld-linux-x86-64.so.2" "${EXE_DIR}"
done

if [[ "${PREVIOUS_BRANCH}" != *"detached"* ]]; then
  echo Switching git branch back to "$PREVIOUS_BRANCH"
  git checkout "$PREVIOUS_BRANCH"
fi