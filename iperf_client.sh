#!/bin/bash

# load variables
. variables.sh

DATE=$(date -I'seconds' | sed -e 's/[ \t]/_/g' -e 's/[:]/_/g' -e 's/T/__H__/')
DUMP_FILE="$DATE".iperf

iperf3 -c "$NET_IPADDR" | tee "$LOGS_PATH"/"$DUMP_FILE"
