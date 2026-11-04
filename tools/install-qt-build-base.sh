#!/bin/sh
# Consistent signed distro toolchain/Qt base; Plasma packages are built separately.
set -eu
[ "$(id -u)" -eq 0 ] && [ -f /etc/arch-release ] || exit 2
[ "$(df -Pk / | awk 'NR==2 {print $4}')" -gt 20971520 ] || exit 2
pacman -Syu --needed --noconfirm base-devel cmake ninja git extra-cmake-modules \
    qt6-base qt6-declarative qt6-wayland qt6-shadertools qt6-svg qt6-virtualkeyboard \
    wayland-protocols
systemctl is-system-running
systemctl --failed --no-pager
printf 'QT CONFIG\n'
grep -E 'QT_FEATURE_(opengles2|egl|eglfs|xcb|opengl)' /usr/include/qt6/QtGui/qtgui-config.h || true
pacman -Q qt6-base qt6-declarative qt6-wayland extra-cmake-modules
