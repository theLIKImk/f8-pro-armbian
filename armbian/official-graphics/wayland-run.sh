#!/bin/sh
set -eu
unset QT_QPA_PLATFORM DISPLAY WAYLAND_DISPLAY
export XDG_SESSION_TYPE=wayland
export XDG_CURRENT_DESKTOP=KDE
export KWIN_COMPOSE=O2
export QT_LOGGING_RULES='kwin*.debug=true;qt.scenegraph.general=true'
exec /usr/bin/kwin_wayland --drm --socket wayland-f8 --exit-with-session /usr/libexec/f8-pro/wayland-client
