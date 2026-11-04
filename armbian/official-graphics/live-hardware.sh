#!/bin/sh
# Driver initialization and offscreen pixel check; no compositor or popup.
PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
mkdir -p /run/f8
exec >/run/f8/graphics-run.log 2>&1
echo 'G6 live driver initialization, automatic popup removed'
modprobe panthor
modprobe panel-simple
timeout -k 5 20 insmod /usr/libexec/f8-pro/f8_gsl_shuping.ko
echo "TOUCH_MODULE_EXIT=$?"
timeout -k 5 30 python3 -I /usr/libexec/f8-pro/gpu-probe.py --output /run/f8/gpu-result.json
echo "GPU_EXIT=$?"
chvt 2 || true
