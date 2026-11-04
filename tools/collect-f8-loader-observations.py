"""Read only selected live physical placement metadata, not RAM or environment."""
import json
from pathlib import Path
import subprocess

P=Path(__file__).resolve().parents[1]
remote=r'''
import json,os
from pathlib import Path
chosen=Path('/proc/device-tree/chosen')
initrd={}
for name in ['linux,initrd-start','linux,initrd-end']:
    path=chosen/name
    if path.exists():
        data=path.read_bytes()
        initrd[name]={'bytes':len(data),'physical_address':hex(int.from_bytes(data,'big'))}
regions=[]
for line in Path('/proc/iomem').read_text().splitlines():
    label=line.split(':',1)[-1].strip()
    if label in ['Kernel code','Kernel data','Kernel bss','System RAM']:
        region=line.split(':',1)[0].strip()
        regions.append({'range':region,'label':label})
print(json.dumps({'scope':'Current old-kernel physical placement metadata only, not new kernel boot or U-Boot environment',
                  'kernel_release':os.uname().release,'chosen_initrd':initrd,'iomem_regions':regions,
                  'kernel_ram_read':False,'uboot_environment_read':False,'device_configuration_changed':False}))
'''
command=['wsl','-d','rg35xx-build','-u','root','--','ssh',
         '-i','/var/tmp/f8-pro-archlinux-20261027/private-keys/f8-pro-test-ed25519',
         '-o','BatchMode=yes','-o','ConnectTimeout=8','-o','IdentitiesOnly=yes',
         '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile=/var/tmp/f8-pro-archlinux-20261027/test-known-hosts',
         'alarm@192.168.1.227','sudo -n python3 -']
r=subprocess.run(command,input=remote,capture_output=True,text=True,encoding='utf-8',timeout=110)
assert r.returncode==0,r.stderr[-500:]
report=json.loads(r.stdout)
(P/'analysis/armbian/live-loader-placement-2026-10-29.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
