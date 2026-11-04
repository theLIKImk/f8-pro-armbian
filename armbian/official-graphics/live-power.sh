#!/bin/sh
PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
mkdir -p /run/f8
while :; do
    timeout -k 2 24 python3 -I /usr/libexec/f8-pro/power-refresh.py --output /run/f8/power-current.json
    sleep 10
done
