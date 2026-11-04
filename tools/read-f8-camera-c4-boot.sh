#!/bin/sh
# Read-only: no open/STREAMON, no module reload, no media graph mutation.
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
def run(args):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=12)
        return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except Exception as e:return {'error':str(e)}
dt=Path('/sys/firmware/devicetree/base/chosen')
checks={
 'cmdline':['cat','/proc/cmdline'],
 'log':['dmesg'],
 'early_init_log':['cat','/run/f8/evaluation-steps.log'],
 'camera_service':['journalctl','-b','-u','f8-camera-start.service','--no-pager'],
 'pending':['cat','/sys/kernel/debug/v4l2-async/pending_async_subdevices'],
 'media':['sh','-c','for m in /dev/media*; do test -e "$m" || continue; media-ctl -d "$m" -p; done'],
 'sensor_bindings':['sh','-c','for d in 5-0037 5-0036; do printf "%s " "$d"; readlink /sys/bus/i2c/devices/$d/driver; done'],
 'health':['sh','-c','cat /proc/sys/kernel/tainted; systemctl is-system-running; systemctl --failed --no-pager'],
}
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
 'chosen':{n:(dt/n).read_bytes().rstrip(b'\0').decode() if (dt/n).exists() else None
           for n in ['f8-camera-trial','f8-camera-async-trial','f8-usb-trial','f8-bluetooth-trial','f8-motion-trial']},
 'checks':{k:run(v) for k,v in checks.items()}},indent=2))
PY
