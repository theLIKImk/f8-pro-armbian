#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
def cmd(args):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=15)
        return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except (OSError,subprocess.TimeoutExpired) as e:return {'error':str(e)}
prefix=['runuser','-u','f8test','--','env','XDG_RUNTIME_DIR=/run/user/1601','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus']
devices={}
for p in Path('/sys/bus/i2c/devices').glob('*-0011'):
    devices[p.name]={'name':(p/'name').read_text().strip() if (p/'name').exists() else None,
                     'driver':str((p/'driver').resolve()) if (p/'driver').is_symlink() else None}
cards=Path('/proc/asound/cards')
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
 'cards':cards.read_text() if cards.exists() else None,'devices':devices,
 'playback':cmd(['aplay','-l']),'mixer':cmd(['amixer','-c','0','scontents']),
 'pipewire':cmd(prefix+['wpctl','status']),
 'sound_log':cmd(['sh','-c',"dmesg | grep -Ei 'es83|asoc|snd|sound|i2s|codec' | tail -100"]),
 'deferred':cmd(['cat','/sys/kernel/debug/devices_deferred'])},indent=2))
PY
