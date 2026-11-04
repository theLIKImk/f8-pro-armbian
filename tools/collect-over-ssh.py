"""Run the collector with the existing desktop session environment on Ubuntu 20.04.

Copy alongside collect-hardware.sh and run as the logged-in desktop user.
Reads only an allowlist of environment fields and never saves the full environment.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

work = Path(sys.argv[1]).resolve()
if os.getuid() == 0:
    raise SystemExit('Run as the desktop user, not root')
collector = work / 'collect-hardware.sh'
allowed = {'DISPLAY', 'XAUTHORITY', 'WAYLAND_DISPLAY', 'XDG_RUNTIME_DIR',
           'XDG_SESSION_TYPE', 'DBUS_SESSION_BUS_ADDRESS'}
environment = os.environ.copy()
selected = None
for process in sorted(Path('/proc').iterdir(), key=lambda p: int(p.name) if p.name.isdigit() else -1):
    if not process.name.isdigit():
        continue
    try:
        if process.stat().st_uid != os.getuid():
            continue
        name = (process / 'comm').read_text().strip()
        if name not in ('gnome-session-b', 'gnome-shell', 'xfce4-session', 'plasmashell', 'kwin_x11', 'kwin_wayland'):
            continue
        values = {}
        for field in (process / 'environ').read_bytes().split(b'\0'):
            key, separator, value = field.partition(b'=')
            if key.decode('ascii', 'ignore') in allowed and separator:
                values[key.decode('ascii')] = value.decode('utf-8', 'surrogateescape')
        if values.get('DISPLAY') or values.get('WAYLAND_DISPLAY'):
            environment.update(values)
            selected = {'pid': int(process.name), 'process': name, 'environment': values}
            break
    except (OSError, ValueError):
        continue
(work / 'desktop-session.json').write_text(json.dumps(selected, indent=2) + '\n')
with (work / 'desktop-collection.log').open('w') as log:
    subprocess.run(['sh', str(collector), str(work / 'desktop'), 'all'],
                   env=environment, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=600)
with (work / 'system-collection.log').open('w') as log:
    privileged = subprocess.run(['sudo', '-n', 'sh', str(collector), str(work / 'system'), 'system'],
                                stdout=log, stderr=subprocess.STDOUT, timeout=600)
if (work / 'system').exists():
    subprocess.run(['sudo', '-n', 'chown', '-R', '{}:{}'.format(os.getuid(), os.getgid()), str(work / 'system')], check=True)
subprocess.run(['tar', '-czf', str(work) + '.tar.gz', '-C', str(work.parent), work.name], check=True)
print('Desktop environment found:', selected is not None)
print('Administrator collection exit:', privileged.returncode)
print('REPORT=' + str(work) + '.tar.gz')
