#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,re,subprocess,time
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='1ca22167-5a98-4f7e-b17c-fec65cd72d5b'
assert '[host]' in Path('/sys/class/typec/port0/data_role').read_text()
assert '[source]' in Path('/sys/class/typec/port0/power_role').read_text()
reg=next(p for p in Path('/sys/class/regulator').glob('*') if (p/'name').exists() and (p/'name').read_text().strip()=='f8_usb_otg_vbus')
assert (reg/'state').read_text().strip()=='enabled'
mask=subprocess.check_output(['systemctl','show','udisks2.service','-p','ActiveState','-p','UnitFileState'],text=True)
assert 'masked-runtime' in mask and 'ActiveState=inactive' in mask
stage=Path('/var/lib/f8-pro/usb-u2-host-mode01');stage.mkdir(exist_ok=False)
mode=Path('/sys/kernel/debug/usb/fc000000.usb/mode')
before=mode.read_text().strip();assert before=='device'
def cmd(args):
    p=subprocess.run(args,capture_output=True,text=True,timeout=15)
    return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
result={'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'mode_before':before,'scope':'Temporary controller role only; no mounts or filesystem writes','udisks':mask}
try:
    mode.write_text('host\n')
    deadline=time.monotonic()+8
    while time.monotonic()<deadline:
        if any(p.name.startswith('sd') and '/usb' in str(p.resolve()) for p in Path('/sys/class/block').glob('*')):break
        time.sleep(0.25)
    result['mode_during']=mode.read_text().strip()
    result['lsusb']=cmd(['lsusb','-t'])
    result['usb_devices']={p.name:{n:(p/n).read_text().strip() for n in ['idVendor','idProduct','product','speed'] if (p/n).exists()} for p in Path('/sys/bus/usb/devices').glob('*') if (p/'idVendor').exists()}
    result['usb_blocks']={p.name:{'path':str(p.resolve()),'sectors':(p/'size').read_text().strip(),'read_only':(p/'ro').read_text().strip()} for p in Path('/sys/class/block').glob('*') if '/usb' in str(p.resolve())}
    mounts=Path('/proc/mounts').read_text().splitlines()
    result['usb_mounts']=[s for s in mounts if any(s.split()[0]=='/dev/'+name for name in result['usb_blocks'])]
    assert not result['usb_mounts'],'Unexpected automatic mount'
    log=cmd(['dmesg']);log['stdout']='\n'.join(s for s in log['stdout'].splitlines() if re.search(r'usb|xhci|scsi|sd |sd\w|Oops|BUG:',s,re.I))[-18000:]
    result['kernel_log']=log
finally:
    mode.write_text(before+'\n')
    time.sleep(0.5)
    result['mode_restored']=mode.read_text().strip()
    (stage/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
PY
