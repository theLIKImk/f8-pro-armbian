#!/bin/sh
set -eu
test -f /etc/armbian-release
test "$(uname -r)" = 6.1.115-vendor-rk35xx
printf 'OFFICIAL_ARMBIAN_LIVE_POWER\n'
uname -r
cat /run/f8/power-current.json
