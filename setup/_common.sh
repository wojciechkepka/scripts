#!/bin/bash

BGREEN='\033[1;32m'
BRED='\033[1;31m'
BWHITE='\033[1;37m'
NC='\033[0m'

function ctrl_c() {
    echo "Exiting..."
    exit 1
}

ask() {
    local msg="$1"
    shift
    echo -e "${BGREEN}$msg y/n${NC}"
    while true
    do
        read -n 1 -s c
        case "$c" in
            "y")
                "$@"
                break
                ;;
            "n")
                break
                ;;
            *)
                ;;
        esac
    done
}

notify() {
    local msg="$1"
    echo "################################################################################"
    echo -e "${BWHITE}INFO: $msg${NC}"
    echo "################################################################################"
}
err() {
    local msg="$1"
    echo "################################################################################"
    echo -e "${BRED}ERROR: $msg${NC}"
    echo "################################################################################"
}

saferun() {
    $@
    if [ $? != 0 ]
    then
        err "failed running '$@'. Error code: '$?'"
        exit 1
    fi
}
