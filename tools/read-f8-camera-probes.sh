#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
def run(args):
    p=subprocess.run(args,capture_output=True,text=True,timeout=12)
    return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
clients={}
for n in ['5-000c','5-0036','5-0037']:
 p=Path('/sys/bus/i2c/devices')/n
 clients[n]={'driver':str((p/'driver').resolve()) if (p/'driver').exists() else None,
  'modalias':(p/'modalias').read_text().strip() if (p/'modalias').exists() else None}
print(json.dumps({'clients':clients,
 'sensor_logs':run(['sh','-c',"dmesg | grep -Ei 'gc5035|ov8858|dw9714|rkisp|pin-102|mipim1|vcc_mipidcphy' | head -90"]),
 'deferred':run(['cat','/sys/kernel/debug/devices_deferred']),
 'gpio':run(['cat','/sys/kernel/debug/gpio']),
 'install':run(['systemctl','show','f8-camera-app-install','-p','ActiveState','-p','SubState','-p','ExecMainStatus']),
 'install_log':run(['journalctl','-u','f8-camera-app-install','-n','25','--no-pager'])},indent=2))
PY
