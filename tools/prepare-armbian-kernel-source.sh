#!/bin/sh
# Separate build workspace. Never touches the tablet or existing Arch sources.
set -eu
base=/var/tmp/f8-pro-armbian
source_dir="$base/linux-rockchip"
expected=85233a85b67928000afc2e966bab86a8c414f1b4
mkdir -p "$base"
if [ ! -e "$source_dir" ]; then
    git clone --depth 1 --single-branch --branch rk-6.1-rkr7.2 \
        https://github.com/armbian/linux-rockchip.git "$source_dir"
fi
actual=$(git -C "$source_dir" rev-parse HEAD)
if [ "$actual" != "$expected" ]; then
    printf 'Source revision mismatch: %s (expected %s); no build performed\n' "$actual" "$expected" >&2
    exit 1
fi
test -z "$(git -C "$source_dir" status --porcelain)"
printf 'Pinned kernel source ready: %s\n' "$actual"
