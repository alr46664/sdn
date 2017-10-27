#!/bin/bash

# protocolos suportados e controller
PROTOCOLS='OpenFlow10,OpenFlow13'
CONTROLLER='tcp:192.168.6.254:6633'

# Nome e MAC da bridge
BRIDGE_IFACE='br-lan-ovs'
BRIDGE_ADDR='00:00:aa:bb:cc:dd'

# configure a bridge e os protocolos do OpenFlow
ovs-vsctl add-br "$BRIDGE_IFACE"
ovs-vsctl set bridge "$BRIDGE_IFACE" other-config:hwaddr="$BRIDGE_ADDR"
ovs-vsctl set bridge "$BRIDGE_IFACE" protocols="$PROTOCOLS"
# nao permita que o OpenVSwitch defina os flows caso nao
# seja possivel conectar ao controller.
# Caso fail-mode=standalone , OpenVSwitch opera como
# learning switch
ovs-vsctl set bridge "$BRIDGE_IFACE" fail_mode=secure

# configure controller
ovs-vsctl set-controller "$BRIDGE_IFACE" "$CONTROLLER"
# nosso controller esta fora da rede gerenciada pelo openvswitch
ovs-vsctl set controller "$BRIDGE_IFACE" connection-mode=out-of-band
ovs-vsctl set bridge "$BRIDGE_IFACE" other-config:disable-in-band=true

# adicione as portas a bridge
ovs-vsctl add-port "$BRIDGE_IFACE" eth0.1
ovs-vsctl add-port "$BRIDGE_IFACE" eth0.3
ovs-vsctl add-port "$BRIDGE_IFACE" eth0.4
ovs-vsctl add-port "$BRIDGE_IFACE" eth0.5
# ovs-vsctl add-port "$BRIDGE_IFACE" wlan0
# ovs-vsctl add-port "$BRIDGE_IFACE" wlan1
