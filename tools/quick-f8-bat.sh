#!/bin/sh
systemctl is-active f8-battery-cw2015.service
ls /sys/class/power_supply/
echo DONE
