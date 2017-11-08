#!/bin/bash

# load variables
. variables.sh

# este script nao so funciona se netmask de variables for 255.255.255.0 !!!

IP_NET=$(echo $NET_IPADDR | grep -o '\([0-9]\{1,3\}\.\)\{3\}')
IP_RANGE=$(echo $NET_IPADDR | sed 's/.*\.//g')

DEVICE=$1
shift

# default do device p8p1
if [ -z "$DEVICE" ]; then
    DEVICE=p8p1
fi

# ESTA ROTINA CRIA O CONTROLLER DO SWITCH
./network_namespace.sh -a "$CTRL_NET_NAMESPACE" "$DEVICE" "$CTRL_IP"/24
./network_namespace.sh -t "$CTRL_NET_NAMESPACE"
