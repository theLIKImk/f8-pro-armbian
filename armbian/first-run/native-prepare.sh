#!/bin/sh
set -eu
test -f /etc/f8-pro-release-r1
mkdir -p /run/f8 /run/sshd /var/lib/f8-pro/first-run
ssh-keygen -A
# Provisioning is part of the image, never recreate a test account or copy a key.
if [ ! -f /var/lib/f8-pro/first-run/complete.json ]; then
    getent passwd f8setup >/dev/null
fi
echo 'F8: local setup ready'
