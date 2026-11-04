#!/bin/sh
echo "=== VIDIOC 失败点前后的内核日志（rkisp 相关）==="
sudo -n dmesg | grep -iE 'rkisp|video22|video31|stream|format' | grep -vE 'apparmor|audit' | tail -25
echo DONE
