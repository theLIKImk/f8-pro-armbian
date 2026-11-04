#!/bin/sh
set -eu
python3 -I - <<'PY'
import fcntl,hashlib,json,subprocess,time,re
from pathlib import Path
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
assert boot=='1ca22167-5a98-4f7e-b17c-fec65cd72d5b'
assert 'f8_usb_u1=1' in Path('/proc/cmdline').read_text()
module=Path('/usr/libexec/f8-pro/f8_otg_vbus_u2.ko')
assert hashlib.sha256(module.read_bytes()).hexdigest()=='a61fdb4cd70d8c60b53341f53e818b7ac0318d8798a92a1cf22c34e12556b39c'
assert not Path('/sys/module/f8_otg_vbus').exists()
stage=Path('/var/lib/f8-pro/usb-u2-load01');stage.mkdir(exist_ok=False)
def cmd(args,timeout=15):
    try:
        r=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
        return {'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
    except (OSError,subprocess.TimeoutExpired) as e:return {'error':str(e)}
def save(d):
    (stage/'result.json').write_text(json.dumps(d,indent=2)+'\n')
result={'boot_id':boot,'started_epoch':time.time(),'charging_policy_initialization':False,
        'udisks_before':cmd(['systemctl','show','udisks2.service','-p','ActiveState','-p','UnitFileState']),
        'power_before':cmd(['systemctl','show','f8-live-power.service','-p','ActiveState','-p','ConditionResult'])}
assert 'ActiveState=inactive' in result['power_before']['stdout']
assert 'ConditionResult=no' in result['power_before']['stdout']
save(result)
override=Path('/run/systemd/journald.conf.d/98-f8-usb-u2.conf')
assert not override.exists();override.parent.mkdir(exist_ok=True)
override.write_text('[Journal]\nStorage=persistent\nSystemMaxUse=32M\nRuntimeMaxUse=8M\n')
Path('/var/log/journal').mkdir(exist_ok=True)
result['journal_restart']=cmd(['systemctl','restart','systemd-journald.service'])
result['journal_flush']=cmd(['journalctl','--flush'])
result['udisks_mask']=cmd(['systemctl','mask','--runtime','udisks2.service'])
assert result['udisks_mask'].get('exit')==0,result['udisks_mask']
result['udisks_stop']=cmd(['systemctl','stop','udisks2.service'])
assert result['udisks_stop'].get('exit')==0,result['udisks_stop']
save(result)
with Path('/run/f8/bq-adc.lock').open('a') as lock:
    fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    result['insmod']=cmd(['insmod',str(module)])
    save(result)
time.sleep(2)
result['module_loaded']=Path('/sys/module/f8_otg_vbus').exists()
result['bindings']={p.name:str((p/'driver').resolve()) if (p/'driver').is_symlink() else None for p in Path('/sys/bus/i2c/devices').glob('6-*')}
result['deferred']=cmd(['cat','/sys/kernel/debug/devices_deferred'])
result['usb_log']=cmd(['dmesg'])
result['usb_log']['stdout']='\n'.join(s for s in result['usb_log'].get('stdout','').splitlines() if re.search(r'usb|fusb|typec|tcpm|vbus|Oops|BUG:|panic|Unknown symbol|version of symbol',s,re.I))[-24000:]
result['udisks_after']=cmd(['systemctl','show','udisks2.service','-p','ActiveState','-p','UnitFileState'])
result['failed_units']=cmd(['systemctl','--failed','--no-legend','--no-pager'])
result['journal_sync']=cmd(['journalctl','--sync'])
save(result);print(json.dumps(result,indent=2))
PY
