#!/bin/bash

. ./_setup.sh

LOCATION=$1
TMPSCRIPTS=$LOCATION/tmp/scripts

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

notify "Bootstraping base system to $LOCATION"
saferun pacstrap $LOCATION ${PACSTRAP_PKGS[@]}

notify "Generating fstab"
genfstab -U $LOCATION >> $LOCATION/etc/fstab

notify "Preparing setup scripts"
mkdir -p $TMPSCRIPTS
saferun cp ./* $TMPSCRIPTS

saferun arch-chroot $LOCATION $TMPSCRIPTS/_setup.sh
