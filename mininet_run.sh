#!/bin/bash

killall ryu-manager 2> /dev/null
sudo mn -c
sudo mn --topo single,3 --mac --switch ovsk --controller remote
