#!/bin/bash

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PWD=$(pwd)

cd "$SCRIPT_DIR" &&
ryu-manager l2switch.py statistics.py
cd "$PWD"
