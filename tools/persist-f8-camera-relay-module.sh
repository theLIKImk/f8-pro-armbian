#!/bin/sh
set -eu
python3 -I - <<'PY'
import json
from pathlib import Path
assert Path('/sys/class/video4linux/video42/name').read_text().strip()=='F8 Camera Relay'
assert Path('/sys/module/v4l2loopback/parameters/max_buffers').read_text().strip()=='2'
other=[str(p) for p in Path('/etc/modprobe.d').glob('*.conf') if 'v4l2loopback' in p.read_text(errors='replace')]
assert not other,other
files={'/etc/modules-load.d/f8-camera-relay.conf':'# Create virtual device only; capture requires user enabling the F8 app relay.\nv4l2loopback\n',
 '/etc/modprobe.d/f8-camera-relay.conf':'options v4l2loopback devices=1 video_nr=42 card_label="F8 Camera Relay" exclusive_caps=1 max_width=640 max_height=480 max_buffers=2\n'}
for n in files:assert not Path(n).exists(),n
for n,s in files.items():p=Path(n);p.write_text(s);p.chmod(0o644)
print(json.dumps({'files':files,'automatic_capture':False,'boot_persistence_tested':False},indent=2))
PY
