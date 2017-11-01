#!/bin/bash

# desative buffer do python pra salvar logs com tee
export PYTHONUNBUFFERED=1

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PWD=$(pwd)
OPTION=$1

cd "$SCRIPT_DIR"

# load variables
. ../variables.sh

DATE=$(date -I'seconds' | sed -e 's/[ \t]/_/g' -e 's/[:]/_/g' -e 's/T/__H__/')
DUMP_FILE=../"$LOGS_PATH"/"$DATE".ofp_stats

if [ "$OPTION" == "$RYU_OPTION_NOLOG" ]; then
    # neste caso, informamos que nao queremos gerar um log
    ryu-manager $RYU_APPS
else
    ryu-manager $RYU_APPS | tee "$DUMP_FILE"
fi
cd "$PWD"
