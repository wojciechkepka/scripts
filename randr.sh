#!/bin/bash

ROTATE="$1"

pkill xrandr

if [[ $ROTATE =~ "rotate" ]]
then
    xrandr --output HDMI-1 --auto --output DP-2 --rotate right --auto --right-of HDMI-1
else
    xrandr --output HDMI-1 --auto --output DP-2 --auto --right-of HDMI-1
fi

