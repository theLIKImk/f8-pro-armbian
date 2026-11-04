#!/bin/sh
set -eu
python3 -I - <<'PY'
from pathlib import Path
p=Path('/etc/udev/rules.d/70-f8-cover-haptic.rules')
s=p.read_text()
line=next(x for x in s.splitlines() if 'F8 Haptic Motor' in x)
if 'FEEDBACKD_TYPE' not in line:
    p.with_suffix('.rules.before-keyboard').write_text(s)
    p.write_text(s.replace(line,line+', ENV{FEEDBACKD_TYPE}="vibra"'))
assert Path('/sys/devices/platform/f8-cover-haptic/motor_active').read_text().strip()=='0'
PY
udevadm control --reload-rules
udevadm trigger --action=change /sys/class/input/$(basename "$(readlink -f /dev/input/f8-haptic)")
udevadm settle
udevadm info -q property /dev/input/f8-haptic
