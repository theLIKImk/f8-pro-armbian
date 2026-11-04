set -eu
[ "$(id -u)" = 0 ]
pacman -Syu --needed --noconfirm meson
systemctl is-system-running
