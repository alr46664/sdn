#!/bin/bash

sudo mn -c
sudo mn --topo single,3 --mac --switch ovsk --controller remote
