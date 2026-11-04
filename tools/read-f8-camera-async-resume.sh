#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
def run(args):
    p=subprocess.run(args,capture_output=True,text=True,timeout=12)
    return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
checks={
 'early_load_prerequisites':['sh','-c','ls -l /usr/sbin/modprobe; modprobe --show-depends gc5035; modprobe --show-depends ov8858; sha256sum /usr/libexec/f8-pro/camera-start.py /etc/systemd/system/f8-camera-start.service; readlink /sys/bus/platform/devices/rkisp0-vir0/driver; readlink /sys/bus/platform/devices/rkisp1-vir0/driver'],
 'cmdline':['cat','/proc/cmdline'],
 'service':['journalctl','-b','-u','f8-camera-start.service','--no-pager'],
 'pending':['cat','/sys/kernel/debug/v4l2-async/pending_async_subdevices'],
 'symbols':['sh','-c',"grep -E ' (rkcif_clr_unready_dev|rkisp_clr_unready_dev|v4l2_async_nf_clear_unready_dev|__initcall.*clr_unready)' /proc/kallsyms"],
 'parameters':['sh','-c','for m in video_rkcif video_rkisp; do for p in /sys/module/$m/parameters/*; do test -f "$p" && printf "%s=" "$p" && cat "$p"; done; done'],
 'log':['dmesg'],
 'health':['sh','-c','cat /proc/sys/kernel/tainted; systemctl is-system-running; systemctl --failed --no-pager'],
}
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'checks':{k:run(v) for k,v in checks.items()}},indent=2))
PY
