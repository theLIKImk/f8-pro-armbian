#!/bin/sh
set -eu
test -f /etc/armbian-release
test "$(uname -r)" = 6.1.115-vendor-rk35xx
python3 -I - <<'PY'
import json,time,subprocess,re
from pathlib import Path
samples=[]
for index in range(6):
    power=json.loads(Path('/run/f8/power-current.json').read_text())
    uptime=float(Path('/proc/uptime').read_text().split()[0])
    assert power['complete'] and 0<=uptime-power['monotonic_seconds']<30
    zones=[]
    for path in sorted(Path('/sys/class/thermal').glob('thermal_zone*')):
        try:zones.append({'zone':path.name,'type':(path/'type').read_text().strip(),'millicelsius':int((path/'temp').read_text())})
        except (OSError,ValueError):pass
    samples.append({'uptime_seconds':uptime,'power_age_seconds':uptime-power['monotonic_seconds'],
        'power':power,'thermal_zones':zones,'loadavg':Path('/proc/loadavg').read_text().strip(),
        'wireless_counters':Path('/proc/net/wireless').read_text()})
    if index<5:time.sleep(8)
def command(args):
    r=subprocess.run(args,capture_output=True,text=True,timeout=5)
    return {'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
dm=command(['dmesg'])
alerts=[line for line in dm['stdout'].splitlines() if re.search(r'Kernel panic|\bOops:|thermal.*(critical|shutdown)|over.?temperature|watchdog.*(lockup|reset)|firmware.*crash',line,re.I)]
print(json.dumps({'scope':'Charger-connected stability, existing passive telemetry only',
 'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'samples':samples,
 'failed_units':command(['systemctl','--no-pager','--failed']),
 'service_states':command(['systemctl','is-active','f8-live-ssh','f8-live-power','f8-live-status']),
 'kernel_alerts':alerts,'battery_temperature_available':False,
 'power_supply_interfaces':[p.name for p in Path('/sys/class/power_supply').iterdir()]},indent=2))
PY
