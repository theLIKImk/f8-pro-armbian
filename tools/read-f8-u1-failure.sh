#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,re,subprocess
from pathlib import Path
def cmd(args):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=20)
        return {'exit':p.returncode,'stdout':p.stdout[-50000:],'stderr':p.stderr[-1500:]}
    except (OSError,subprocess.TimeoutExpired) as e:return {'error':str(e)}
def read(p):
    try:return p.read_text(errors='replace')[-30000:]
    except OSError:return None
pattern=re.compile(r'f8_usb|f8-otg|f8_otg|fusb|tcpm|typec|usb|dwc3|regulator|panic|Oops|BUG:|INIT STOP|power.service|init-failed|Unknown symbol|version of symbol',re.I)
previous=cmd(['journalctl','-b','-1','--no-pager','-o','short-monotonic'])
previous['stdout']='\n'.join(s for s in previous.get('stdout','').splitlines() if pattern.search(s))
print(json.dumps({'boot_id':read(Path('/proc/sys/kernel/random/boot_id')),'cmdline':read(Path('/proc/cmdline')),
 'boots':cmd(['journalctl','--list-boots','--no-pager']), 'previous_boot_filtered':previous,
 'pstore':{p.name:read(p) for p in Path('/sys/fs/pstore').glob('*') if p.is_file()},
 'u1_power_dropin':read(Path('/etc/systemd/system/f8-live-power.service.d/98-f8-usb-u1.conf')),
 'current_power':cmd(['systemctl','show','f8-live-power.service','-p','ActiveState','-p','SubState','-p','ConditionResult']),
 'current_failed':cmd(['systemctl','--failed','--no-legend','--no-pager']),
 'scope':'Read-only U1 failure evidence after A3 rollback; no charger/GPIO/role writes'},indent=2))
PY
