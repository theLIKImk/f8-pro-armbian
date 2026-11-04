#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,subprocess
from pathlib import Path
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();assert boot=='3f9b409e-0860-438a-a5eb-2ac768dbafd2'
usb=Path('/sys/bus/usb/devices/1-1');assert (usb/'idVendor').read_text().strip()=='152d' and (usb/'idProduct').read_text().strip()=='0583'
assert (usb/'speed').read_text().strip()=='480'
assert '[host]' in Path('/sys/class/typec/port0/data_role').read_text()
assert '[source]' in Path('/sys/class/typec/port0/power_role').read_text()
root=next(s.split() for s in Path('/proc/mounts').read_text().splitlines() if s.split()[1]=='/');assert root[0]=='/dev/mmcblk0p6' and 'rw' in root[3].split(',')
services={}
for service in ['f8-usb-otg','sddm','f8-live-ssh','NetworkManager']:
    services[service]=subprocess.check_output(['systemctl','is-active',service],text=True).strip();assert services[service]=='active'
blocks={p.name:{'sectors':int((p/'size').read_text()),'partition':(p/'partition').exists()} for p in Path('/sys/class/block').glob('*') if str(p.resolve()).startswith(str(usb.resolve())+'/')}
assert any(not d['partition'] and d['sectors']>100000000 for d in blocks.values())
mounts=[]
for line in Path('/proc/mounts').read_text().splitlines():
    s=line.split()
    if s[0] in ['/dev/'+name for name in blocks]:mounts.append({'source':s[0],'filesystem':s[2],'options':s[3]})
udisks=subprocess.check_output(['systemctl','show','udisks2.service','-p','ActiveState','-p','UnitFileState'],text=True)
assert 'masked' not in udisks and 'ActiveState=active' in udisks
failed=subprocess.check_output(['systemctl','--failed','--no-legend','--no-pager'],text=True);assert not failed.strip()
print(json.dumps({'boot_id':boot,'auto_loaded_driver_and_usb_enumeration_passed':True,'services':services,'blocks':blocks,'mounts':mounts,'udisks':udisks,'failed_units':failed,'usb_speed_mbps':480,'root_rw':True,'agent_write_test_performed':False},indent=2))
PY
