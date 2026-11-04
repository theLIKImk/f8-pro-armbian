#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,re,subprocess,time
from pathlib import Path
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();assert boot=='a262ec8f-29d5-4110-a7f0-f82dc0034611'
assert '[host]' in Path('/sys/class/typec/port0/data_role').read_text()
assert '[source]' in Path('/sys/class/typec/port0/power_role').read_text()
assert Path('/sys/kernel/debug/usb/fc000000.usb/mode').read_text().strip()=='host'
state=subprocess.check_output(['systemctl','show','udisks2.service','-p','ActiveState','-p','UnitFileState'],text=True)
assert 'masked-runtime' in state and 'ActiveState=inactive' in state
mode=Path('/sys/bus/platform/devices/fd5d0000.syscon:usb2-phy@0/otg_mode');before=mode.read_text().strip();assert before=='otg'
stage=Path('/var/lib/f8-pro/usb-u3-phy-host01');stage.mkdir(exist_ok=False)
def cmd(args):
    p=subprocess.run(args,capture_output=True,text=True,timeout=15)
    return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
result={'boot_id':boot,'phy_before':before,'scope':'Temporary driver-provided PHY mode attribute; no mounts or filesystem writes'}
try:
    mode.write_text('host\n')
    deadline=time.monotonic()+8
    while time.monotonic()<deadline:
        if any('/usb' in str(p.resolve()) and p.name.startswith('sd') for p in Path('/sys/class/block').glob('*')):break
        time.sleep(0.25)
    result['phy_during']=mode.read_text().strip();result['lsusb']=cmd(['lsusb','-t'])
    result['usb_devices']={p.name:{n:(p/n).read_text().strip() for n in ['idVendor','idProduct','product','speed'] if (p/n).exists()} for p in Path('/sys/bus/usb/devices').glob('*') if (p/'idVendor').exists()}
    result['usb_blocks']={p.name:{'path':str(p.resolve()),'sectors':(p/'size').read_text().strip(),'read_only':(p/'ro').read_text().strip()} for p in Path('/sys/class/block').glob('*') if '/usb' in str(p.resolve())}
    result['usb_mounts']=[s for s in Path('/proc/mounts').read_text().splitlines() if any(s.split()[0]=='/dev/'+n for n in result['usb_blocks'])]
    assert not result['usb_mounts']
    result['kernel_log']=cmd(['dmesg']);result['kernel_log']['stdout']='\n'.join(s for s in result['kernel_log']['stdout'].splitlines() if re.search(r'usb|xhci|scsi|sd |sd\w|Oops|BUG:',s,re.I))[-14000:]
finally:
    mode.write_text(before+'\n');result['phy_restored']=mode.read_text().strip()
    (stage/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
PY
