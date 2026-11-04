set -eu
[ "$(id -u)" = 0 ]
if pgrep -x makepkg >/dev/null; then echo 'Build active; defer package transaction'; exit 2; fi
if pgrep -x pacman >/dev/null; then echo 'pacman busy'; exit 2; fi
pacman -Syu --needed --noconfirm weston
weston --version
weston --help | head -n 95
systemctl is-system-running
