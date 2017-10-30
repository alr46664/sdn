#!/bin/bash

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

TOPOLOGY='single,3'

sudo mn -c
konsole -e "$SCRIPT_DIR/ryu/run.sh" &
sudo mn --topo "$TOPOLOGY" --mac --switch ovsk --controller remote
killall ryu-manager 2> /dev/null
