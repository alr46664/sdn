#!/bin/bash

# configuracoes do roteador
INTERFACE_OVS=br-lan-ovs
ROUTER_IP=192.168.6.1
ROUTER_SSH=root@$ROUTER_IP

# controller
CTRL_NET_NAMESPACE=openflow
CTRL_IP=192.168.6.254

# configuracoes da rede OpenFlow
NET_IPADDR=192.168.1.1
NET_NETMASK=255.255.255.0

# pasta de logs
LOGS_PATH=logs
