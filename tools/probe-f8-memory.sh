#!/bin/sh
set -eu
printf 'LOADER-PROVIDED MEMORY\n'
find /sys/firmware/devicetree/base -maxdepth 1 -name 'memory*' -type d | while IFS= read -r d; do
    printf '%s\n' "${d##*/}"
    [ ! -f "$d/reg" ] || od -An -tx1 -v "$d/reg"
done
printf 'RESERVED MEMORY\n'
for d in /sys/firmware/devicetree/base/reserved-memory/*; do
    [ -d "$d" ] || continue
    printf '%s ' "${d##*/}"
    [ ! -f "$d/reg" ] || od -An -tx1 -v "$d/reg"
done
printf '\nMEMINFO\n'
head -n 3 /proc/meminfo
printf '\nCPU REGULATOR CLIENTS\n'
for d in /sys/bus/i2c/devices/0-0042 /sys/bus/i2c/devices/0-0043; do
    printf '%s\n' "${d##*/}"
    cat "$d/name"
    readlink "$d/driver" || true
done
