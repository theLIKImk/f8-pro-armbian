#!/bin/sh
# Binary tar output: pipe directly to a private file, never to a text logger.
set -eu
[ "$(id -u)" -eq 0 ] && [ -f /etc/arch-release ] || exit 2
[ "$(findmnt -n -o SOURCE /)" = /dev/mmcblk0p6 ] || exit 2
cd /
set -- etc home/alarm var/lib/f8-pro
if [ -f var/lib/systemd/random-seed ]; then set -- "$@" var/lib/systemd/random-seed; fi
tar --exclude='etc/pacman.d/gnupg/S.gpg-agent*' -czf - "$@"
