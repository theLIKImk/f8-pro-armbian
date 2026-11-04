set -eu
printf '\nINSTALL PROCESSES\n'
pgrep -a pacman || true
printf '\nPACKAGES\n'
pacman -Q qt6-base qt6-declarative qt6-wayland qt6-virtualkeyboard extra-cmake-modules cmake ninja gcc 2>&1 || true
printf '\nSYSTEM\n'
systemctl is-system-running || true
systemctl --failed --no-pager
printf '\nPACMAN RECENT\n'
tail -n 15 /var/log/pacman.log
printf '\nQT FEATURES\n'
grep -E 'QT_FEATURE_(opengles2|egl|eglfs|xcb|opengl)' /usr/include/qt6/QtGui/qtgui-config.h || true
