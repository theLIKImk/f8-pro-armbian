#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,os,subprocess,time
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='9df01d2b-d624-4364-8d3d-a06ff6847720'
usb=Path('/sys/bus/usb/devices/1-1')
assert (usb/'idVendor').read_text().strip()=='152d' and (usb/'idProduct').read_text().strip()=='0583'
state=subprocess.check_output(['systemctl','show','udisks2.service','-p','ActiveState','-p','UnitFileState'],text=True)
assert 'masked-runtime' in state and 'ActiveState=inactive' in state
def cmd(args):
    p=subprocess.run(args,capture_output=True,text=True,timeout=15)
    return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
blocks={}
for p in Path('/sys/class/block').glob('*'):
    if str(usb.resolve())+'/' not in str(p.resolve()):continue
    blocks[p.name]={'sectors':int((p/'size').read_text()),'logical_block_size':int((p/'queue/logical_block_size').read_text()) if (p/'queue/logical_block_size').exists() else None,'partition':(p/'partition').exists()}
assert blocks and any(not d['partition'] and d['sectors']>100000000 for d in blocks.values()),blocks
mounts=[s for s in Path('/proc/mounts').read_text().splitlines() if any(s.split()[0]=='/dev/'+name for name in blocks)]
assert not mounts,mounts
for name,d in blocks.items():
    dev=Path('/dev')/name
    probe=cmd(['blkid','-p','-o','export',str(dev)])
    d['filesystem_metadata']={k:v for line in probe['stdout'].splitlines() if '=' in line for k,v in [line.split('=',1)] if k in ['TYPE','PTTYPE','PART_ENTRY_TYPE','BLOCK_SIZE']}
    if not d['partition']:
        fd=os.open(dev,os.O_RDONLY|os.O_CLOEXEC)
        try:
            started=time.monotonic();data=os.pread(fd,4096,0)
            assert len(data)==4096
            d['read_test']={'bytes':len(data),'seconds':time.monotonic()-started,'write_operations':0,'data_not_saved_or_printed':True}
        finally:os.close(fd)
    d['bytes']=d['sectors']*512
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'usb_speed_mbps':(usb/'speed').read_text().strip(),'blocks':blocks,'usb_mounts':mounts,'udisks':state,'read_only_metadata_and_read_test_passed':True},indent=2))
PY
