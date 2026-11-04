#!/bin/sh
set -eu
find /home/f8test/.config -maxdepth 3 -type f | sed 's|/home/f8test/||' | sort
find /home/f8test/.local/share/applications /home/f8test/Desktop /var/lib/f8-pro -maxdepth 3 -type f 2>/dev/null | sort
grep -R -n -E '1601|f8test|/home/' /usr/local/bin /usr/local/lib/f8-pro /usr/libexec/f8-pro /etc/systemd/system /etc/udev/rules.d /etc/wireplumber /etc/pipewire /etc/polkit-1/rules.d 2>/dev/null | head -90
