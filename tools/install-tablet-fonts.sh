set -eu
[ "$(id -u)" = 0 ]
if pgrep -x pacman >/dev/null; then echo 'pacman busy'; exit 2; fi
pacman -Syu --needed --noconfirm noto-fonts noto-fonts-cjk
fc-match sans-serif
fc-match 'sans-serif:lang=zh-cn'
fc-list | wc -l
systemctl is-system-running
