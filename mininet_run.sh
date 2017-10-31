#!/bin/bash

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

TOPOLOGY='single,3'

sudo mn -c
sudo mn --topo "$TOPOLOGY" --mac --switch ovsk --controller remote
