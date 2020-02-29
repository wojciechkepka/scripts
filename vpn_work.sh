#!/bin/bash

VPN_NAMESERVER="16.193.144.1"
HOME_NAMESERVER="192.168.0.2"
RESOLV="/etc/resolv.conf"
VPN_CONF="/home/wojtek/vpn/openvpn.ovpn"

################################################################################

replace_resolv() {
	local new_nameserver="$1"

	if [ -f $RESOLV ]
	then
		sudo sh -c "cat > $RESOLV <<- EOF
		nameserver $new_nameserver
		EOF"
	else
		echo "Warning: file '$RESOLV' doesn't exist so not replacing the nameserver"
	fi
}

trap ctrl_c INT
ctrl_c() {
	echo "closing openvpn"
	sudo pkill openvpn

	replace_resolv $HOME_NAMESERVER	
	exit 0
}

################################################################################

command -v openvpn >/dev/null
if [ $? -ne 0 ]
then
	echo "Error: openvpn executable not found, exitting"
	exit 1
fi

if [ -f $VPN_CONF ]
then
	replace_resolv $VPN_NAMESERVER
	sudo openvpn $VPN_CONF
else
	echo "Error: openvpn config missing from '$VPN_CONF'"
	exit 1
fi
