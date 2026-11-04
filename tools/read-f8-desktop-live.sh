#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
def command(args):
    r=subprocess.run(args,capture_output=True,text=True,timeout=10)
    return {'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
prefix=['runuser','-u','f8test','--','env','XDG_RUNTIME_DIR=/run/user/1601','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1601/bus']
parts={}
for name in ['mmcblk0p3','mmcblk0p6']:
    node=Path('/sys/class/block')/name
    parts[name]={'start_sectors':int((node/'start').read_text()),'size_sectors':int((node/'size').read_text()),
      'blkid':command(['blkid','-p','-o','export','/dev/'+name])}
print(json.dumps({'scope':'Real Plasma compositor/input and partition layout probe',
 'session':json.loads(Path('/run/user/1601/f8-desktop/session.json').read_text()),
 'kwin_support':command(prefix+['busctl','--user','call','org.kde.KWin','/KWin','org.kde.KWin','supportInformation']),
 'virtual_keyboard':command(prefix+['busctl','--user','introspect','org.kde.KWin','/VirtualKeyboard']),
 'user_process_names':command(['ps','-u','1601','-o','comm=']),
 'parts':parts,'mounts':Path('/proc/mounts').read_text(),
 'zstd_available':Path('/usr/bin/zstd').exists(),
 'sddm_state':command(['systemctl','show','sddm','-p','ActiveState','-p','SubState','-p','Result'])},indent=2))
PY
