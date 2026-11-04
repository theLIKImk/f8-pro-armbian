#!/bin/sh
grep -H . /sys/class/video4linux/*/name | grep -E 'stream_cif|scale_ch|tools_id' | head -12
echo "---async:"
sudo -n dmesg | grep -iE 'v4l2.*async|notifier' | tail -6
echo DONE
