#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,subprocess
from pathlib import Path
def run(args,timeout=12):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
        return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except Exception as e:return {'error':str(e)}
processes=[]
allowed=['--ozone-platform','--enable-features','--disable-features','--enable-blink-features','--disable-blink-features','--type','--no-sandbox','--disable-seccomp-filter-sandbox']
for p in Path('/proc').glob('[0-9]*'):
    try:
        args=(p/'cmdline').read_bytes().decode().split('\0')
        if args and any(s in Path(args[0]).name.lower() for s in ['chromium','chrome']):
            processes.append({'pid':int(p.name),'exe':os.readlink(p/'exe'),'flags':[a for a in args[1:] if any(a==x or a.startswith(x+'=') for x in allowed)]})
    except (OSError,UnicodeError):pass
devices={}
for p in Path('/sys/bus/iio/devices').glob('iio:device*'):
    devices[str(p)]={'name':(p/'name').read_text().strip(),'attributes':[f.name for f in p.iterdir() if f.is_file()],
     'udev':run(['udevadm','info','--query=property','--path='+str(p)])}
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'processes':processes,'devices':devices,
 'commands':{'version':run(['chromium','--version']),'packages':run(['sh','-c',"dpkg-query -W '*chromium*' '*udev*' 2>/dev/null"]),
 'flatpak':run(['flatpak','info','org.chromium.Chromium']),'snap':run(['snap','list','chromium']),
 'read_access':run(['runuser','-u','f8test','--','sh','-c','for d in /sys/bus/iio/devices/iio:device*; do echo "$d"; for f in "$d"/in_accel_x_raw "$d"/in_anglvel_x_raw "$d"/in_magn_x_raw; do if [ -f "$f" ]; then test -r "$f" && echo "readable: $f"; fi; done; done'])}},indent=2))
PY
