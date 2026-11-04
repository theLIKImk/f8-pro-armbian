#!/bin/sh
set -eu
python3 -I - <<'PY'
import json,time
from pathlib import Path
def read(p,limit=24000):
    try:
        with p.open() as f:return f.read(limit)
    except OSError as e:return {'error':str(e)}
regmaps={}
for p in Path('/sys/kernel/debug/regmap').glob('*'):
    if any(s in p.name for s in ['fd5d0000','fd5ac000']):
        regs={}
        try:
            with (p/'registers').open() as f:
                for line in f:
                    left,sep,right=line.partition(':')
                    if not sep:continue
                    address=int(left,16)
                    if address>0x100:break
                    if address in [0,4,8,12,16,20,24,28,64,128,132,136,192]:regs[hex(address)]=right.strip()
        except OSError as e:regs['error']=str(e)
        regmaps[p.name]=regs
root=Path('/sys/kernel/debug/usb/xhci')
paths=[str(p) for p in root.glob('*/*/*')] if root.exists() else []
portfiles={}
if root.exists():
    for p in root.glob('*/*/*'):
        if p.is_file() and p.name in ['portsc','port_status','reg-op']:portfiles[str(p)]=read(p)
dump=read(Path('/sys/kernel/debug/usb/fc000000.usb/regdump'))
if isinstance(dump,str):dump='\n'.join(s for s in dump.splitlines() if any(k in s for k in ['GCTL','GUSB2PHYCFG','GUSB3PIPECTL','GFLADJ','GUCTL']))
print(json.dumps({'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'regmaps':regmaps,'dwc3_registers':dump,'xhci_paths':paths[:80],'xhci_port_files':portfiles,'scope':'Kernel debugfs read only; no direct memory/register writes'},indent=2))
PY
