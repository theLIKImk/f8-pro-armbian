#!/bin/sh
# Extract a host-side Debian tool into this task's directory; no host installation.
set -eu
base=/var/tmp/f8-pro-armbian/host-tools
mkdir -p "$base/downloads" "$base/root"
cd "$base/downloads"
apt-get download squashfs-tools liblzo2-2 > "$base/download.log" 2>&1
for package in ./*_amd64.deb; do
    test -f "$package"
    dpkg-deb --extract "$package" "$base/root"
done
export LD_LIBRARY_PATH="$base/root/usr/lib/x86_64-linux-gnu:$base/root/lib/x86_64-linux-gnu"
"$base/root/usr/bin/mksquashfs" -version > "$base/version.txt"
cat "$base/version.txt"
