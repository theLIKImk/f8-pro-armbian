set -eu
[ "$(id -u)" = 0 ]
if pgrep -x makepkg >/dev/null; then echo 'build busy'; exit 2; fi
pacman -Syu --needed --noconfirm kcolorscheme kglobalaccel kguiaddons kiconthemes kio kirigami knotifications kpackage ksvg kwidgetsaddons kwindowsystem qt6-5compat kdoctools
systemctl is-system-running
