#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess,os
from pathlib import Path
def cmd(args):
    try:
        r=subprocess.run(args,capture_output=True,text=True,timeout=15)
        return {'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
    except (OSError,subprocess.TimeoutExpired) as e:return {'error':str(e)}
def read(p):
    try:return Path(p).read_text().strip()
    except OSError:return None
prefix=['runuser','-u','f8test','--','env','XDG_RUNTIME_DIR=/run/user/1601','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus']
backlights={}
for p in Path('/sys/class/backlight').glob('*'):
    backlights[p.name]={k:read(p/k) for k in ['brightness','actual_brightness','max_brightness','bl_power','type']}
services=cmd(['systemctl','show','sddm','f8-desktop-hardware','f8-live-status','f8-live-ssh','NetworkManager','bluetooth',
              '-p','Id','-p','ActiveState','-p','SubState','-p','Result'])
print(json.dumps({'scope':'T1r2 non-battery read-only baseline','boot_id':read('/proc/sys/kernel/random/boot_id'),
 'kernel':os.uname().release,'root_mount':next(x for x in Path('/proc/mounts').read_text().splitlines() if x.split()[1]=='/'),
 'services':services,'handoff':read('/etc/systemd/system/sddm.service.d/96-f8-status-handoff.conf'),
 'failed':cmd(['systemctl','--failed','--no-pager']),
 'session':read('/run/user/1601/f8-desktop/session.json'),
 'kwin':cmd(prefix+['busctl','--user','call','org.kde.KWin','/KWin','org.kde.KWin','supportInformation']),
 'keyboard':cmd(prefix+['busctl','--user','introspect','org.kde.KWin','/VirtualKeyboard']),
 'outputs':cmd(prefix+['kscreen-doctor','-o']),
 'audio_cards':read('/proc/asound/cards'),'alsa_devices':cmd(['aplay','-l']),
 'backlight':backlights,'bluetooth_nodes':[x.name for x in Path('/sys/class/bluetooth').glob('*')],
 'rfkill':cmd(['rfkill','list']),'inputs':read('/proc/bus/input/devices'),
 'audio_bt_kernel':cmd(['sh','-c',"dmesg | grep -Ei 'es83|asoc|snd|sound|bluetooth|hci|backlight' | tail -60"])
},indent=2))
PY
