#!/bin/sh
# Optional: explicitly run on the tablet AFTER the initial unmodified collection.
set -eu
LC_ALL=C
export LC_ALL
. /etc/os-release
if [ "${ID:-}" != ubuntu ] || [ "${VERSION_ID:-}" != 20.04 ]; then
    echo 'This helper targets the original Ubuntu 20.04 installation.' >&2
    exit 1
fi
if [ "$(id -u)" -ne 0 ]; then exec sudo sh "$0" "$@"; fi
apt-get update
# Query candidates on the actual configured vendor repositories; do not change sources.
packages=''
for package in mesa-utils mesa-utils-extra alsa-utils v4l-utils pciutils usbutils; do
    if apt-cache policy "$package" | grep -Eq 'Candidate: [^ (]'; then
        packages="$packages $package"
    else
        printf 'No package candidate, skipped: %s\n' "$package"
    fi
done
if [ -n "$packages" ]; then
    # Package names come only from the fixed list above.
    plan=$(mktemp /tmp/f8-diagnostic-packages.XXXXXXXX)
    trap 'rm -f -- "$plan"' EXIT HUP INT TERM
    apt-get --simulate --no-install-recommends --no-remove --no-upgrade install $packages >"$plan"
    cat "$plan"
    if grep -Eq '^Inst [^ ]+ \[' "$plan"; then
        echo 'Existing package upgrades would be needed. Stop and retain the original baseline.' >&2
        exit 1
    fi
    apt-get install --no-install-recommends --no-remove --no-upgrade $packages
fi
printf 'Tools prepared. Run the collection launcher again as the desktop user.\n'
