#!/bin/sh
set -eu
python3 -I - <<'PY'
import subprocess
from pathlib import Path
assert Path('/sys/class/video4linux/video42/name').read_text().strip()=='F8 Camera Relay'
p=subprocess.run(['fuser','/dev/video42'],capture_output=True,text=True);assert not p.stdout.strip()
assert sorted(p.name for p in Path('/sys/devices/virtual/video4linux').glob('video*'))==['video42']
subprocess.run(['modprobe','-r','v4l2loopback'],check=True,timeout=8)
subprocess.run(['modprobe','v4l2loopback','devices=1','video_nr=42','card_label=F8 Camera Relay','exclusive_caps=1','max_width=640','max_height=480','max_buffers=2'],check=True,timeout=8)
subprocess.run(['udevadm','settle','--timeout=8'],check=True,timeout=10)
print('Virtual loopback only: default two buffers, no physical driver reload')
PY
