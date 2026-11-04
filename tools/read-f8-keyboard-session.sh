#!/bin/sh
set -eu
export XDG_RUNTIME_DIR=/run/user/1601
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus
gdbus introspect --session --dest org.kde.KWin --object-path /VirtualKeyboard
pgrep -af plasma-keyboard
find /usr/share/plasma/keyboard -type f | head -10
grep -R -n -E 'vibrationEnabled|Vibration.vibrate' /usr/share/plasma/keyboard /usr/lib/aarch64-linux-gnu/qt6/qml/org/kde/plasma/keyboard 2>/dev/null || true
python3 -I - <<'PY'
import subprocess,os
p=int(subprocess.check_output(['pgrep','-u',str(os.getuid()),'-x','plasma-keyboard'],text=True).strip())
print('\n'.join(x for x in open(f'/proc/{p}/environ').read().split('\0') if x.startswith(('PLASMA_KEYBOARD','QT_VIRTUALKEYBOARD','WAYLAND_DISPLAY'))))
PY
