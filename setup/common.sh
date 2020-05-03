#!/bin/bash

function ctrl_c() {
	echo "Exiting..."
	exit 1
}

ask() {
	local msg="$1"
	shift
	echo "$msg y/n"
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
	echo "INFO: $msg"
	echo "################################################################################"
}
