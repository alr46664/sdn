#!/bin/bash

# desative buffer do python pra salvar logs com tee
export PYTHONUNBUFFERED=1

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PWD=$(pwd)

cd "$SCRIPT_DIR"

# load variables
. ../variables.sh

DATE=$(date -I'seconds' | sed -e 's/[ \t]/_/g' -e 's/[:]/_/g' -e 's/T/__H__/')
DUMP_FILE=../"$LOGS_PATH"/"$DATE".ofp_stats

ryu-manager $RYU_APPS | tee "$DUMP_FILE"
cd "$PWD"
