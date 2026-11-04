set -eu
printf '\nWESTON PACKAGE\n'
pacman -Si weston | head -n 30
printf '\nSEAT PACKAGES\n'
pacman -Q libseat seatd weston 2>&1 || true
printf '\nVIRTUAL TERMINALS\n'
ls -l /dev/tty0 /dev/tty1 /dev/dri/card0
printf '\nKDE BUILD\n'
tail -n 6 /home/alarm/f8-pro-builds/kwayland-6.7.5-3z75XnjZ/build.log
