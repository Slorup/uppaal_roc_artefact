#!/bin/bash
# Use this script when the native dynamic linker is imcompatible
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  HERE=$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)
  SOURCE=$(readlink "$SOURCE")
  [[ "$SOURCE" != /* ]] && SOURCE="$HERE/$SOURCE"
done
HERE=$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)
export LD_LIBRARY_PATH="$HERE"
B=verifyta
exec "$HERE"/$B "$@"
#exec -a $B "$HERE"/libc.so.6 "$HERE"/libgcc_s.so.1 "$HERE"/$B "$@"