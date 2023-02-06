#!/bin/bash
set -e

REMOTE_PORT=9000
PROTOCOL="udp"
IP="192.168.1.0/24"

if [ `whoami` != root ]; then
    echo "Please run this script using sudo"
    exit
fi

COMMAND_LINE_OPTIONS_HELP="
Usage:  $0 block [protocol] [remote_port] [ip]
        $0 unblock [protocol] [remote_port] [ip]
        $0 flush
        $0 list
"

usage() {
   echo "$COMMAND_LINE_OPTIONS_HELP"
   exit 3
}

block()
{
    #iptables -A OUTPUT -p ${PROTOCOL} --dport ${REMOTE_PORT} -s ${IP} -j DROP
    #iptables -A INPUT -p ${PROTOCOL} --sport ${REMOTE_PORT} -d ${IP} -j DROP
    iptables -A FORWARD -p ${PROTOCOL} --dport ${REMOTE_PORT} -s ${IP} -j DROP
    iptables -A FORWARD -p ${PROTOCOL} --sport ${REMOTE_PORT} -d ${IP} -j DROP
}

unblock()
{
    #iptables -D OUTPUT -p ${PROTOCOL} --dport ${REMOTE_PORT} -s ${IP} -j DROP
    #iptables -D INPUT -p ${PROTOCOL} --sport ${REMOTE_PORT} -d ${IP} -j DROP
    iptables -D FORWARD -p ${PROTOCOL} --dport ${REMOTE_PORT} -s ${IP} -j DROP
    iptables -D FORWARD -p ${PROTOCOL} --sport ${REMOTE_PORT} -d ${IP} -j DROP
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
    if [ "$#" -ne 4 ]; then
        usage
    fi
    echo "block $2 for remote port $3 for $4"
    PROTOCOL=$2
    REMOTE_PORT=$3
    IP=$4
    block
    ;;

unblock)
    if [ "$#" -ne 4 ]; then
        usage
    fi
    echo "unblock $2 for remote port $3 for $4"
    PROTOCOL=$2
    REMOTE_PORT=$3
    IP=$4
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
