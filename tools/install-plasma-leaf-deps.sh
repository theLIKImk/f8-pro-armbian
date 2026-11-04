set -eu
[ "$(id -u)" = 0 ]
if pgrep -x pacman >/dev/null; then echo 'pacman busy'; exit 2; fi
pacman -Syu --needed --noconfirm plasma-wayland-protocols qt6-positioning kdbusaddons kholidays ki18n
systemctl is-system-running
