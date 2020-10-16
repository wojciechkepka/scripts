#!/bin/bash

. ./_setup.sh

LOCATION=$1

if [ -z "$LOCATION" ]
then
    echo "USAGE:
    setup.sh <location>"

    exit 1
fi


PACSTRAP_PKGS=(
    'base'
    'linux'
    'linux-firmware'
    'lvm2'
    'mdadm'
    'dhcpcd'
)


pacstrap $LOCATION ${PACSTRAP_PKGS[@]}
genfstab -U $LOCATION >> $LOCATION/etc/fstab
arch-chroot $LOCATION
setup
