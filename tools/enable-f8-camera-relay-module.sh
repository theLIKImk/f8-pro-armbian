#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
assert subprocess.check_output(['uname','-r'],text=True).strip()=='6.1.115-vendor-rk35xx'
assert not Path('/sys/module/v4l2loopback').exists(),'Preserve existing loopback configuration'
assert not Path('/dev/video42').exists(),'Preserve existing video device'
magic=subprocess.check_output(['modinfo','-F','vermagic','v4l2loopback'],text=True).strip();assert magic=='6.1.115-vendor-rk35xx SMP mod_unload modversions aarch64'
subprocess.run(['modprobe','v4l2loopback','devices=1','video_nr=42','card_label=F8 Camera Relay','exclusive_caps=1','max_width=640','max_height=480','max_buffers=4'],check=True,timeout=12)
subprocess.run(['udevadm','settle','--timeout=8'],check=True,timeout=10)
assert Path('/sys/class/video4linux/video42/name').read_text().strip()=='F8 Camera Relay'
print(json.dumps({'device':'/dev/video42','vermagic':magic,'temporary_load':True,'camera_capture_started':False}))
PY
