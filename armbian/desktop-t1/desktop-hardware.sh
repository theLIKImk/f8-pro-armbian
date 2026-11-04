#!/bin/sh
set -eu
PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
mkdir -p /run/f8
exec >/run/f8/graphics-run.log 2>&1
echo 'F8 desktop T1 hardware initialization, no test popup'
modprobe panthor
modprobe panel-simple
timeout -k 5 20 insmod /usr/libexec/f8-pro/f8_gsl_shuping.ko
if ! timeout -k 5 40 python3 -I /usr/libexec/f8-pro/gpu-probe.py --output /run/f8/gpu-result.json; then
    echo 'Offscreen EGL diagnostic inconclusive; continue to the actual KWin Wayland session'
fi
chvt 2 || true
echo 'F8 DESKTOP: GPU/panel/touch modules loaded; actual rendering must be checked in KWin'
