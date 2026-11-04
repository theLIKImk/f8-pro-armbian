#!/bin/sh
set -eu
test -f /etc/armbian-release
test "$(uname -r)" = 6.1.115-vendor-rk35xx
python3 -I - <<'PY'
import json,time,subprocess
from pathlib import Path
samples=[]
for number in range(4):
    data=json.loads(Path('/run/f8/power-current.json').read_text())
    uptime=float(Path('/proc/uptime').read_text().split()[0])
    assert data['complete'] and 0<=uptime-data['monotonic_seconds']<30
    samples.append({'uptime_seconds':uptime,'age_seconds':uptime-data['monotonic_seconds'],'power':data})
    if number<3:time.sleep(10)
failed=subprocess.run(['systemctl','--no-pager','--failed'],capture_output=True,text=True,timeout=10)
print(json.dumps({'scope':'User confirms external charger connected; passive observations only',
 'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
 'samples':samples,'failed_units':failed.stdout},indent=2))
PY
