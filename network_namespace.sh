#!/bin/bash

# defina erros do script
ERR_NETNS_BLK=255
ERR_NETNS_EXIST=254
ERR_NETNS_NOT_EXIST=253
ERR_DEVICE_NOT_EXIST=252
ERR_IP_CIDR_FORMAT=251

# defina as opcoes do script
OPTION_ADD='-a'
OPTION_DEL='-d'
OPTION_WIRESHARK='-w'
OPTION_FIREFOX='-f'
OPTION_TERMINAL='-t'

# arquivo de configuracao dos network namespaces
CONF="netns.conf"

OPTION=$(echo $1 | xargs)
shift

# namespace a ser criado
NAMESPACE=$(echo $1 | xargs)
shift

# interfaces fisicas a serem adicionadas ao namespace
DEVICES=$@

display_help(){
    echo -e '\n\tCopyright  Andre Luiz Romano Madureira 2017 (License GNU GPLv3)'
    echo -e '\n\tnetork_namespace.sh OPTION namespace [device1 ip_cidr1] [device2 ip_cidr2] [...]\n'
    echo -e 'OPTION\tDESCRIPTION'
    echo -e "$OPTION_ADD"'\tadd devices to namespace'
    echo -e "$OPTION_DEL"'\tdelete namespace'
    echo -e "$OPTION_WIRESHARK"'\topen wireshark'
    echo -e "$OPTION_FIREFOX"'\topen firefox'
    echo -e "$OPTION_TERMINAL"'\topen terminal'
    echo -e '-h\topen help'
    echo -e '\n'
    exit 0
}

check_netns(){
    if [ -z "$NAMESPACE" ]; then
        echo -e "\n\tERROR: NAMESPACE IS IN BLANK (NULL NAME)\n"
        exit $ERR_NETNS_BLK
    fi
    if ip netns list | grep "$NAMESPACE" &> /dev/null; then
        # we know netns exists
        if [ "$1" == "-n" ]; then
            # but it should not exist (null parameter -n has been passed)
            echo -e "\n\tERROR: \"$NAMESPACE\" NAMESPACE ALREADY EXISTS\n"
            exit $ERR_NETNS_EXIST
        fi
    elif [ "$1" != "-n" ]; then
        # we know netns DOES NOT exist and it should
        # (we didnt pass the null parameter -n)
        echo -e "\n\tERROR: \"$NAMESPACE\" NAMESPACE DOES NOT EXIST\n"
        exit $ERR_NETNS_NOT_EXIST
    fi
}

check_devices(){
    while [ $# -ne 0 ]; do
        DEVICE=$1
        IP_CIDR=$2
        shift; shift
        if !(ip link list | grep "$DEVICE") || [ -z "$DEVICE" ]; then
            echo -e "\n\tERROR: \"$DEVICE\" DEVICE DOES NOT EXIST\n"
            exit $ERR_DEVICE_NOT_EXIST
        fi
        if [ -z "$IP_CIDR" ]; then
            echo -e "\n\tERROR: \"$IP_CIDR\" MALFORMED\n"
            exit $ERR_IP_CIDR_FORMAT
        fi
    done
}

del_netns(){
    sudo ip netns delete "$NAMESPACE"
}

add_device(){
    DEVICE="$1"
    IP_CIDR="$2"
    sudo ip link set dev "$DEVICE" netns "$NAMESPACE"
    sudo ip netns exec "$NAMESPACE" ifconfig "$DEVICE" "$IP_CIDR" up
}

add_netns(){
    # crie um novo namespace e mostre as interfaces conectadas a ele
    sudo ip netns add "$NAMESPACE"
    # adione os devices ao namespace
    DEVICES_ADD=''
    while [ $# -ne 0 ]; do
        DEVICE=$1
        IP_CIDR=$2
        shift; shift
        DEVICES_ADD="$DEVICES_ADD $DEVICE"
        echo "$DEVICE" "$IP_CIDR"
        add_device "$DEVICE" "$IP_CIDR"
    done
    # teste pra ver se os devices estao no namespace
    sudo ip netns exec "$NAMESPACE" ip netns identify
    sudo ip netns exec "$NAMESPACE" ip link list
    echo -e "\tNamespace \"$NAMESPACE\" created SUCESSFULLY - Devices: \"$DEVICES_ADD\" - ADDED\n"
}


case $OPTION in
    $OPTION_ADD)
        check_netns -n
        check_devices $DEVICES
        add_netns $DEVICES
        ;;
    $OPTION_DEL)
        check_netns
        del_netns
        ;;
    $OPTION_WIRESHARK)
        check_netns
        kdesu ip netns exec "$NAMESPACE" wireshark
        ;;
    $OPTION_FIREFOX)
        check_netns
        kdesu ip netns exec "$NAMESPACE" firefox
        ;;
    $OPTION_TERMINAL)
        check_netns
        # sudo ip netns exec "$NAMESPACE" bash -c 'export PS1='"$NAMESPACE"'_ns\ \$\  ; bash'
        sudo ip netns exec "$NAMESPACE" bash
        ;;
    *)
        display_help
        ;;
esac

