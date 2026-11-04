#!/bin/sh
set -eu
export XDG_RUNTIME_DIR=/run/user/1601
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus
cat /usr/share/dbus-1/interfaces/org.sigxcpu.Feedback.Haptic.xml
gdbus introspect --session --dest org.sigxcpu.Feedback --object-path /org/sigxcpu/Feedback
pgrep -af feedbackd
strings /usr/libexec/feedbackd | grep -E 'Haptic|Vibrate|rumble' || true
python3 -I - <<'PY'
import dbus,json,time
from pathlib import Path
p=Path('/sys/devices/platform/f8-cover-haptic/motor_active')
i=dbus.Interface(dbus.SessionBus().get_object('org.sigxcpu.Feedback','/org/sigxcpu/Feedback'),'org.sigxcpu.Feedback.Haptic')
try:
    result=i.Vibrate('org.kde.plasma.keyboard',dbus.Array([dbus.Struct((dbus.Double(1.0),dbus.UInt32(30)))],signature='(du)'))
    time.sleep(.01); a=p.read_text().strip();time.sleep(.12)
    print(json.dumps({'result':bool(result),'at_10ms':a,'at_130ms':p.read_text().strip()}))
except Exception as e: print(type(e).__name__,str(e));raise
PY
