"""Atomically add a verified evaluation SquashFS under a new original-root directory."""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time

P=Path(__file__).resolve().parents[1]
source=P/'outputs/armbian/evaluation-wayland/rootfs.squashfs'
size=936742912
expected='a69fdacdc7ad5fc1d9239ffb271c40bb2e05fb151e0635c2f59b2ef70885a8dc'
assert source.stat().st_size==size
with source.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==expected
prefix=['wsl','-d','rg35xx-build','-u','root','--','ssh',
 '-i','/var/tmp/f8-pro-archlinux-20261027/private-keys/f8-pro-test-ed25519',
 '-o','BatchMode=yes','-o','ConnectTimeout=8','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=4',
 '-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes',
 '-o','UserKnownHostsFile=/var/tmp/f8-pro-archlinux-20261027/test-known-hosts','alarm@192.168.1.227']
probe=r'''
import hashlib,json,os
from pathlib import Path
p=Path('/var/lib/f8-pro/armbian-evaluation/rootfs.squashfs')
assert os.uname().release=='5.10.160' and Path('/etc/arch-release').is_file()
for node in [Path('/var/lib/f8-pro'),p.parent,p]:
    assert not node.is_symlink()
report={'kernel_release':os.uname().release,'arch_present':True,'target_exists':p.exists()}
if p.exists():
    assert p.is_file()
    with p.open('rb') as stream:report['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
    report['bytes']=p.stat().st_size
print(json.dumps(report))
'''
def remote_code(code,**kwargs):
    return subprocess.run(prefix+['sudo -n python3 -c '+shlex.quote(code)],capture_output=True,text=True,timeout=180,**kwargs)
r=remote_code(probe);assert r.returncode==0,r.stderr[-500:]
before=json.loads(r.stdout)
started=time.monotonic()
if before['target_exists']:
    assert before['sha256']==expected and before['bytes']==size,'Existing different file preserved; choose a new version/path'
    result={**before,'reused_existing_verified_file':True}
else:
    writer=r'''
import hashlib,json,os,shutil,sys
from pathlib import Path
directory=Path('/var/lib/f8-pro/armbian-evaluation')
expected='a69fdacdc7ad5fc1d9239ffb271c40bb2e05fb151e0635c2f59b2ef70885a8dc'
size=936742912
assert os.uname().release=='5.10.160' and Path('/etc/arch-release').is_file()
for node in [Path('/var/lib/f8-pro'),directory]:assert not node.is_symlink()
directory.mkdir(parents=True,exist_ok=True,mode=0o700)
assert shutil.disk_usage(directory).free>size+2*1024**3
part=directory/'.rootfs.squashfs.upload-20261029.part'
target=directory/'rootfs.squashfs'
assert not target.exists() and not target.is_symlink()
checksum=hashlib.sha256();total=0
with part.open('xb') as output:
    os.chmod(part,0o600)
    while True:
        chunk=sys.stdin.buffer.read(1024*1024)
        if not chunk:break
        total+=len(chunk);assert total<=size
        output.write(chunk);checksum.update(chunk)
    output.flush();os.fsync(output.fileno())
assert total==size and checksum.hexdigest()==expected
os.link(part,target) # exclusive destination creation; never replace an existing file
part.unlink()
fd=os.open(directory,os.O_DIRECTORY);os.fsync(fd);os.close(fd)
with target.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
assert actual==expected
print(json.dumps({'remote_path':str(target),'bytes':total,'sha256':actual,
                  'reused_existing_verified_file':False,'atomic_verified_publish':True}))
'''
    with source.open('rb') as stream:
        r=subprocess.run(prefix+['sudo -n python3 -c '+shlex.quote(writer)],stdin=stream,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=1200)
    assert r.returncode==0,r.stderr[-600:]
    result=json.loads(r.stdout)
report={'scope':'Added evaluation data file only; no boot/config/partition changes or reboot',
        **result,'elapsed_seconds':round(time.monotonic()-started,1),
        'source_project_relative_path':source.relative_to(P).as_posix(),
        'original_arch_ssh_confirmed':True,'image_executed_on_tablet':False}
(P/'analysis/armbian/userspace/tablet-rootfs-staging.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
