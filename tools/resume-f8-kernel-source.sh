#!/bin/sh
# Complete the pinned partial clone; keep logs and never run concurrent Git writes.
set -eu
base=/var/tmp/f8-pro-armbian
source_dir="$base/linux-rockchip-config"
project=/mnt/d/Netdisk/Other/F8-PRO/archlinux
report="$project/analysis/armbian/kernel-build"
mkdir -p "$report"
exec 9>"$base/source-completion.lock"
flock -n 9 || { echo 'Source completion already running' >&2; exit 1; }
test ! -e "$source_dir/.git/index.lock"
test "$(git -C "$source_dir" rev-parse HEAD)" = 85233a85b67928000afc2e966bab86a8c414f1b4
date -u +%FT%TZ > "$report/source-completion.started"
set +e
timeout --signal=TERM --kill-after=30s 600s git -C "$source_dir" \
    -c http.version=HTTP/1.1 sparse-checkout disable \
    > "$report/source-completion.log" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$report/source-completion.exit"
date -u +%FT%TZ > "$report/source-completion.finished"
if [ "$status" -ne 0 ]; then
    echo "Source completion failed or timed out ($status); see source-completion.log" >&2
    exit "$status"
fi
test -f "$source_dir/mm/mmap.c"
test -z "$(git -C "$source_dir" status --porcelain)"
printf 'Pinned source checkout complete\n'
