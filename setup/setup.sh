#!/bin/bash

. ./_common.sh

LOCATION=$1
TMPSCRIPTS=/bld/scripts
TMPLOCAL=$LOCATION/$TMPSCRIPTS

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

bootstrap_pkgs() {
    notify "Bootstraping base system to $LOCATION"
    saferun pacstrap $LOCATION ${PACSTRAP_PKGS[@]}
}

generate_fstab() {
    notify "Generating fstab"
    genfstab -U $LOCATION >> $LOCATION/etc/fstab
}

run_setup() {
    notify "Preparing setup scripts"
    mkdir -p $TMPLOCAL
    saferun cp ./* $TMPLOCAL

    saferun arch-chroot $LOCATION bash -c "cd $TMPSCRIPTS && bash _setup.sh"

    rm -rf $TMPLOCAL
}

ask "Bootstrap initial packages?" bootstrap_pkgs
ask "Generate fstab?" generate_fstab
ask "Run setup?" run_setup
