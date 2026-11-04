set -eu
tail -n 7 /home/alarm/f8-pro-builds/kwayland-6.7.5-3z75XnjZ/build.log
pgrep -x makepkg >/dev/null && echo MAKEPKG_RUNNING || true
