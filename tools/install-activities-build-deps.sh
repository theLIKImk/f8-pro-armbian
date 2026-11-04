set -eu
[ "$(id -u)" = 0 ]
if pgrep -x pacman >/dev/null; then echo 'pacman busy'; exit 2; fi
pacman -Syu --needed --noconfirm kconfig kcoreaddons qt6-tools
pacman -Q kconfig kcoreaddons qt6-tools qt6-base qt6-declarative
systemctl is-system-running
