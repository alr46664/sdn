#!/bin/bash

INTERFACE='s1'

OPTION=$1
shift


case $OPTION in
-del)
  sudo ovs-ofctl del-flows "$INTERFACE" $@
  ;;
-dump)
  sudo ovs-ofctl dump-flows "$INTERFACE" $@
  ;;
esac
