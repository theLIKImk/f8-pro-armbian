#!/bin/sh
set -eu
test -f /etc/armbian-release
test "$(uname -r)" = 6.1.115-vendor-rk35xx
python3 -I - <<'PY'
import json,os,subprocess,time
from pathlib import Path
def command(args):
    r=subprocess.run(args,capture_output=True,text=True,timeout=12)
    return {'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
power=json.loads(Path('/run/f8/power-current.json').read_text())
uptime=float(Path('/proc/uptime').read_text().split()[0])
report={'scope':'G6 r5 authenticated SSH baseline before charger swap',
 'uname':os.uname().release,'hostname':os.uname().nodename,'effective_uid':os.geteuid(),
 'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
 'uptime_seconds':uptime,'power_age_seconds':uptime-power['monotonic_seconds'],
 'power':power,'os_release':Path('/etc/os-release').read_text(),
 'units':command(['systemctl','show','f8-live-prepare.service','f8-live-network.service','f8-live-ssh.service',
 'f8-live-power.service','f8-live-status.service','f8-official-graphics.service','f8-official-wayland.service',
 '-p','Id','-p','ActiveState','-p','SubState','-p','Result','-p','ExecMainStatus']),
 'failed_units':command(['systemctl','--no-pager','--failed']),
 'ip':command(['ip','-4','-o','addr','show','scope','global']),
 'gpu':json.loads(Path('/run/f8/gpu-result.json').read_text()) if Path('/run/f8/gpu-result.json').exists() else None,
 'mounts':Path('/proc/mounts').read_text(),'snapshot_host_time_untrusted':time.time()}
assert report['effective_uid']==0 and power['complete']
assert 0<=report['power_age_seconds']<30
print(json.dumps(report,indent=2))
PY
