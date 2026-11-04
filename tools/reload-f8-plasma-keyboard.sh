#!/bin/sh
set -eu
export XDG_RUNTIME_DIR=/run/user/1601
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus
python3 -I - <<'PY'
import dbus,time,subprocess
b=dbus.SessionBus()
p=dbus.Interface(b.get_object('org.kde.KWin','/VirtualKeyboard'),'org.freedesktop.DBus.Properties')
print('before',subprocess.check_output(['pgrep','-af','/usr/bin/plasma-keyboard'],text=True))
try:
    p.Set('org.kde.kwin.VirtualKeyboard','enabled',dbus.Boolean(False))
    time.sleep(1)
finally:
    p.Set('org.kde.kwin.VirtualKeyboard','enabled',dbus.Boolean(True))
time.sleep(2)
print('after',subprocess.check_output(['pgrep','-af','/usr/bin/plasma-keyboard'],text=True))
PY
