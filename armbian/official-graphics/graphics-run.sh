#!/bin/sh
PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH
umask 077
mkdir -p /run/f8
exec >/run/f8/graphics-run.log 2>&1
echo 'Official Armbian GPU/Wayland bounded test'
modprobe panthor
modprobe panel-simple
timeout -k 5 40 python3 -I /usr/libexec/f8-pro/gpu-probe.py --output /run/f8/gpu-result.json
gpu_result=$?
echo "GPU_EXIT=$gpu_result"
if [ "$gpu_result" -ne 0 ]; then
    echo 'Wayland test skipped because hardware GPU acceptance failed'
    exit 0
fi
chvt 1 || true
timeout 10 systemctl start f8-official-wayland.service
wayland_start=$?
echo "WAYLAND_START=$wayland_start"
if [ "$wayland_start" -eq 0 ]; then sleep 25; fi
timeout 10 systemctl stop f8-official-wayland.service
echo "WAYLAND_STOP=$?"
echo 'Graphics test complete; physical picture requires user confirmation'
