"""Read and verify current BOOT partition for rollback; never write the tablet."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from inspect_images import fdt
P=Path(__file__).resolve().parents[1]
out=P/'outputs/armbian/firstboot-diagnostic'
out.mkdir(parents=True,exist_ok=True)
prefix=['wsl','-d','rg35xx-build','-u','root','--','ssh',
 '-i','/var/tmp/f8-pro-archlinux-20261027/private-keys/f8-pro-test-ed25519',
 '-o','BatchMode=yes','-o','ConnectTimeout=8','-o','IdentitiesOnly=yes',
 '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile=/var/tmp/f8-pro-archlinux-20261027/test-known-hosts','alarm@192.168.1.227']
remote=r'''
import json,subprocess
from pathlib import Path
dev=Path('/dev/disk/by-partuuid/7a3f0000-0000-446a-8000-702f00006273').resolve()
assert dev.exists() and dev.name=='mmcblk0p3'
uuid=subprocess.check_output(['blkid','-s','PARTUUID','-o','value',str(dev)],text=True).strip().lower()
assert uuid=='7a3f0000-0000-446a-8000-702f00006273'
sys=Path('/sys/class/block')/dev.name
start=int((sys/'start').read_text());sectors=int((sys/'size').read_text())
assert start==0x8000 and sectors==0x20000
print(json.dumps({'device':str(dev),'partuuid':uuid,'start_lba':start,'sectors':sectors,'bytes':sectors*512}))
'''
r=subprocess.run(prefix+['sudo -n python3 -'],input=remote,capture_output=True,text=True,encoding='utf-8',timeout=110)
assert r.returncode==0,r.stderr[-400:]
metadata=json.loads(r.stdout)
destination=out/'CURRENT-BOOT-ROLLBACK-64MiB.img'
with destination.open('wb') as stream:
    r=subprocess.run(prefix+['sudo -n dd if=/dev/mmcblk0p3 bs=1048576 count=64 status=none'],stdout=stream,stderr=subprocess.PIPE,timeout=150)
assert r.returncode==0,r.stderr[-400:]
assert destination.stat().st_size==metadata['bytes']
with destination.open('rb') as stream:checksum=hashlib.file_digest(stream,'sha256').hexdigest()
r=subprocess.run(prefix+['sudo -n sha256sum /dev/mmcblk0p3'],capture_output=True,text=True,timeout=110)
assert r.returncode==0 and r.stdout.split()[0]==checksum
blob=destination.read_bytes();tree=fdt(blob);payloads=[]
for path,props in tree.items():
    if not path.startswith('/images/') or path.count('/')!=2:continue
    offset=int.from_bytes(props['data-position'],'big');size=int.from_bytes(props['data-size'],'big')
    assert offset+size<=len(blob)
    digest=hashlib.sha256(blob[offset:offset+size]).digest()
    assert tree[path+'/hash']['value']==digest
    payloads.append({'name':path.rsplit('/',1)[-1],'bytes':size,'sha256':digest.hex()})
report={'scope':'Verified readback of current BOOT only; no device writes or reboot',**metadata,
 'file':destination.name,'sha256':checksum,'remote_partition_sha256_matches':True,
 'fit_payload_hashes_verified':payloads,'device_written':False}
(out/'rollback-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
