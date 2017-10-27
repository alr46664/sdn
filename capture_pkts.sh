#!/bin/bash

INTERFACE=br-lan-ovs

# limite de pacotes
PKT_LIMIT=15

# configuracoes do roteador
SSH_CONFIG=root@192.168.6.1
SFTP_CONFIG=$SSH_CONFIG:/root

# options
OPTION_LIST=-l
OPTION_CAPTURE=-c

DATE=$(date -I'seconds' | sed -e 's/[ \t]/_/g' -e 's/[:]/_/g' -e 's/T/__H__/')
DUMP_FILE="$DATE".pcap

OPTION=$1
shift

display_help(){
    echo -e '\n\tCopyright  Andre Luiz Romano Madureira 2017 (License GNU GPLv3)'
    echo -e '\n\tcapture.sh OPTION [interface]\n'
    echo -e 'OPTION\tDESCRIPTION'
    echo -e "$OPTION_LIST"'\tlist interfaces to listen in the router'
    echo -e "$OPTION_CAPTURE"'\tcapture pacotes de interface (pressione Ctrl + C para finalizar captura)'
    echo -e '-h\topen help'
    echo -e '\n'
    exit 0
}


case $OPTION in
   $OPTION_LIST)
      ssh "$SSH_CONFIG" tcpdump -D
      ;;
   $OPTION_CAPTURE)
      if [ -n "$1" ]; then
        INTERFACE=$1
        shift
      fi
      echo -e '\n\tCAPTURA INICIADA - Pression CTRL + C para TERMINAR\n'
      ssh "$SSH_CONFIG" tcpdump -w "$DUMP_FILE" -i "$INTERFACE"
      sftp -b <( echo "get $DUMP_FILE" ) "$SFTP_CONFIG" &&
      ssh "$SSH_CONFIG" rm "$DUMP_FILE"
      ;;
   *)
     display_help
     ;;
esac

