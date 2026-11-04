#!/bin/sh
grep -H . /sys/class/video4linux/*/name 2>/dev/null
echo DONE
