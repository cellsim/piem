#!/bin/bash
set -e

REMOTE_PORT=9000
PROTOCOL="udp"

if [ `whoami` != root ]; then
    echo "Please run this script using sudo"
    exit
fi

COMMAND_LINE_OPTIONS_HELP="
Usage:  $0 block [protocol] [remote_port]
        $0 unblock [protocol] [remote_port]
        $0 flush
        $0 list
"

usage() {
   echo "$COMMAND_LINE_OPTIONS_HELP"
   exit 3
}

block()
{
    iptables -A OUTPUT -p ${PROTOCOL} --dport ${REMOTE_PORT} -j DROP
    iptables -A INPUT -p ${PROTOCOL} --sport ${REMOTE_PORT} -j DROP
    iptables -A FORWARD -p ${PROTOCOL} --dport ${REMOTE_PORT} -j DROP
    iptables -A FORWARD -p ${PROTOCOL} --sport ${REMOTE_PORT} -j DROP
}

unblock()
{
    iptables -D OUTPUT -p ${PROTOCOL} --dport ${REMOTE_PORT} -j DROP
    iptables -D INPUT -p ${PROTOCOL} --sport ${REMOTE_PORT} -j DROP
    iptables -D FORWARD -p ${PROTOCOL} --dport ${REMOTE_PORT} -j DROP
    iptables -D FORWARD -p ${PROTOCOL} --sport ${REMOTE_PORT} -j DROP
}

flush()
{
    iptables --flush
}

list()
{
    iptables -L
}


case "$1" in

block)
    if [ "$#" -ne 3 ]; then
        usage
    fi
    echo "block $2 for remote port $3"
    PROTOCOL=$2
    REMOTE_PORT=$3
    block
    ;;

unblock)
    if [ "$#" -ne 3 ]; then
        usage
    fi
    echo "unblock $2 for remote port $3"
    PROTOCOL=$2
    REMOTE_PORT=$3
    unblock
    ;;

flush)
    flush
    ;;

list)
    list
    ;;

*)
    usage 
    ;;

esac
