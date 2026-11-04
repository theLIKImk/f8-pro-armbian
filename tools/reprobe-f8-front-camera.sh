#!/bin/sh
echo 'Disabled: do not rebuild a live media graph; use the cold-start path.' >&2
exit 1
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
assert Path('/sys/bus/i2c/devices/5-0037/driver').resolve().name=='gc5035'
assert Path('/sys/firmware/devicetree/base/chosen/f8-camera-trial').read_bytes()==b'c1\0'
prefix=['runuser','-u','f8test','--','env','XDG_RUNTIME_DIR=/run/user/1601','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus']
subprocess.run(prefix+['systemctl','--user','stop','f8-camera-test.service'],capture_output=True,timeout=15)
pending=Path('/sys/kernel/debug/v4l2-async/pending_async_subdevices')
before=pending.read_text() if pending.exists() else None
dev=Path('/sys/bus/platform/devices/csi2-dphy1');driver=(dev/'driver').resolve();assert driver.name=='rockchip-csi2-dphy'
try:
 (driver/'unbind').write_text('csi2-dphy1\n')
 (driver/'bind').write_text('csi2-dphy1\n')
except Exception:
 if not (dev/'driver').exists():(driver/'bind').write_text('csi2-dphy1\n')
 raise
result={'pending_before':before,'pending_after':pending.read_text() if pending.exists() else None,'media':{}}
for p in Path('/dev').glob('media*'):
 r=subprocess.run(['media-ctl','-d',str(p),'-p'],capture_output=True,text=True,timeout=10)
 result['media'][str(p)]={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
print(json.dumps(result,indent=2))
PY
