set -eu
for path in \
 /home/alarm/f8-pro-builds/plasma-activities-6.7.5-Cl4QcUFV/gnupg \
 /home/alarm/f8-pro-builds/layer-shell-qt-6.7.5-gTPkBGDM/gnupg \
 /home/alarm/f8-pro-builds/knighttime-6.7.5-RglMD5hc/gnupg \
 /home/alarm/f8-pro-builds/kwayland-6.7.5-3z75XnjZ/gnupg; do
 [ -d "$path" ] || continue
 gpgconf --homedir "$path" --kill gpg-agent || true
done
printf '\nSYSTEM\n'
systemctl is-system-running
systemctl --failed --no-pager
printf '\nTEMPORARY WAYLAND UNITS\n'
systemctl list-units 'f8-wayland-*' --no-pager
printf '\nSESSIONS\n'
loginctl list-sessions --no-pager
printf '\nACTIVE PROCESSES\n'
pgrep -a weston || true
pgrep -a makepkg || true
