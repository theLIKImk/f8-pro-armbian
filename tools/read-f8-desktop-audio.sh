#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
def cmd(args):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=12)
        return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except (OSError,subprocess.TimeoutExpired) as e:return {'error':str(e)}
prefix=['runuser','-u','f8test','--','env','XDG_RUNTIME_DIR=/run/user/1601','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus']
ucm=Path('/usr/share/alsa/ucm2/ucm.conf')
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'controls':cmd(['amixer','-c','0','controls']),
 'mixer':cmd(['amixer','-c','0','scontents']),'card_info':cmd(['alsactl','info','0']),
 'default_sink':cmd(prefix+['pactl','get-default-sink']),'cards':cmd(prefix+['pactl','--format=json','list','cards']),
 'sinks':cmd(prefix+['pactl','--format=json','list','sinks']),'ucm_verbs':cmd(['alsaucm','-c','hw:0','list','_verbs']),
 'ucm_lookup':ucm.read_text() if ucm.exists() else None,'ucm_dirs':[str(p) for p in Path('/usr/share/alsa/ucm2/conf.d').glob('*') if any(s in p.name.lower() for s in ['rockchip','es83','multicodec'])]},indent=2))
PY
