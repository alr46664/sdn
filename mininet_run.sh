#!/bin/bash

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

IP_BASE=15.0.0.0/8
TOPOLOGY='single,3'

OPTION=$@

case $OPTION in
-n)
   MN_OPTIONS=--nat
   ;;
*)
   ;;
esac

sudo mn -c
sudo mn --topo "$TOPOLOGY" --ipbase "$IP_BASE" $MN_OPTIONS  --mac --switch ovsk --controller remote
