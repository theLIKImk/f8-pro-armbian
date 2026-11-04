#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
def run(args,timeout=10):
    p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
sockets=[p.name for p in Path('/run/user/1601').glob('wayland-*') if p.is_socket()]
user=['runuser','-u','f8test','--','env','XDG_RUNTIME_DIR=/run/user/1601','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus','QT_QPA_PLATFORM=wayland','WAYLAND_DISPLAY='+(sockets[0] if sockets else 'wayland-0')]
print(json.dumps({'monitor_as_root':run(['timeout','4','monitor-sensor','--accel'],7),
 'display':run(user+['kscreen-doctor','-j']),
 'proxy_log':run(['journalctl','-u','iio-sensor-proxy','-n','20','--no-pager']),
 'orientation':run(['busctl','get-property','net.hadess.SensorProxy','/net/hadess/SensorProxy','net.hadess.SensorProxy','AccelerometerOrientation'])},indent=2))
PY
