#!/usr/bin/python3
"""Fixed-purpose privileged LED helper; all timing limits are in the kernel."""
import os,sys
from pathlib import Path
if len(sys.argv)!=2 or sys.argv[1] not in ['pulse','off']:raise SystemExit('Use pulse or off')
if os.geteuid()!=0:raise SystemExit('Administrator authorization required')
if not Path('/proc/device-tree/model').read_bytes().startswith(b'F8-PRO'):raise SystemExit('Unsupported device')
led=Path('/sys/class/leds/f8:white:flash')
if not str(led.resolve()).startswith('/sys/devices/platform/f8-flash/'):raise SystemExit('Flash driver unavailable')
if (led/'max_brightness').read_text().strip()!='1':raise SystemExit('Unexpected LED interface')
(led/'brightness').write_text('1\n' if sys.argv[1]=='pulse' else '0\n')
print('ok')
