#!/bin/sh
set -eu
project=/mnt/d/Netdisk/Other/F8-PRO/archlinux
base=/var/tmp/f8-pro-armbian
rootfs="$base/rootfs-trixie-evaluation"
evidence="$project/analysis/armbian/repository"
mkdir -p "$base/keycheck" "$rootfs/usr/share/keyrings"
chmod 700 "$base/keycheck"
for name in official pinned-build; do
    gpg --homedir "$base/keycheck" --batch --with-colons --show-keys "$evidence/$name.key" \
        > "$evidence/$name-key-details.txt" 2> "$evidence/$name-key-diagnostics.txt"
    awk -F: '$1=="pub" { p=1; next } p && $1=="fpr" { print $10; exit }' \
        "$evidence/$name-key-details.txt" > "$base/$name.fingerprint"
done
cmp "$base/official.fingerprint" "$base/pinned-build.fingerprint"
# Current repository key, confirmed in the pinned official build/config/armbian.key.
# The older 2019 image-signing fingerprint is not the current repository key.
grep -qx 8CFA83D13EB2181EEF5843E41EB30FAF236099FE "$base/official.fingerprint"
gpg --homedir "$base/keycheck" --batch --yes --dearmor \
    --output "$rootfs/usr/share/keyrings/f8-armbian-archive.gpg" "$evidence/official.key"
cat > "$rootfs/etc/apt/sources.list.d/f8-armbian.sources" <<'EOF'
Types: deb
URIs: https://apt.armbian.com
Suites: trixie
Components: main
Architectures: arm64
Signed-By: /usr/share/keyrings/f8-armbian-archive.gpg
EOF
cat > "$rootfs/etc/apt/preferences.d/f8-armbian" <<'EOF'
Package: *
Pin: origin apt.armbian.com
Pin-Priority: 100
EOF
chroot "$rootfs" apt-get -o Acquire::Languages=none update > "$base/armbian-apt-update.log" 2>&1
chroot "$rootfs" apt-cache policy linux-image-vendor-rk35xx linux-headers-vendor-rk35xx linux-dtb-vendor-rk35xx \
    > "$evidence/kernel-package-policy.txt"
cp "$base/armbian-apt-update.log" "$evidence/"
printf 'Armbian key fingerprint verified against pinned build; repository metadata accepted\n'
