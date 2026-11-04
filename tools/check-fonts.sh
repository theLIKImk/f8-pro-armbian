set -eu
printf '\nSYSTEM\n'
systemctl is-system-running || true
systemctl --failed --no-pager
printf '\nFONT MATCH\n'
fc-match sans-serif || true
fc-match 'sans-serif:lang=zh-cn' || true
printf '\nFONT COUNT\n'
fc-list | wc -l
printf '\nFONT PACKAGES\n'
pacman -Q noto-fonts noto-fonts-cjk ttf-dejavu 2>&1 || true
printf '\nRECENT BOOT\n'
cat /proc/uptime
printf '\nROOT\n'
df -h /
