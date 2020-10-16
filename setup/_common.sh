#!/bin/bash

BGREEN='\033[1;32m'
BWhite='\033[1;37m'
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
    echo -e "${BWhite}INFO: $msg${NC}"
    echo "################################################################################"
}
