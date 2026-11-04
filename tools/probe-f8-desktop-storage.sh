#!/bin/sh
set -eu
test -f /etc/armbian-release
python3 -I - <<'PY'
import json,os
from pathlib import Path
p=Path('/run/f8/container')
assert (p/'etc/arch-release').is_file()
v=os.statvfs(p)
print(json.dumps({'kernel':os.uname().release,'container_available_bytes':v.f_bavail*v.f_frsize,
 'container_size_bytes':v.f_blocks*v.f_frsize,'mount_lines':[s for s in Path('/proc/mounts').read_text().splitlines() if '/run/f8/container ' in s],
 'current_root_image_present':(p/'var/lib/f8-pro/armbian-official-26.8.1/rootfs.squashfs').is_file()},indent=2))
PY
