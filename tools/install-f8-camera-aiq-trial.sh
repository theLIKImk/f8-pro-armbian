#!/bin/sh
set -eu
python3 -I - <<'PY'
import hashlib,json,os,subprocess,tarfile
from pathlib import Path
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='532eb6df-13ce-4e63-9645-24d4136d96b9'
archive=Path('/home/f8test/.cache/f8-camera-aiq-c4-stage/aiq-trial.tar.gz')
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='c273ff5181b7aed1cdc8f8bb358e13644cdd694f6c0fc8f45fd2e27b11f36982'
root=Path('/opt/f8-pro-camera/aiq-v6-c4');assert not root.exists()
with tarfile.open(archive) as tar:
    members=tar.getmembers();manifest=json.load(tar.extractfile('manifest.json'))
    assert len(members)==len(manifest['files'])+1
    for m in members:assert m.isfile() and m.name in [*manifest['files'],'manifest.json']
    data={n:tar.extractfile(n).read() for n in manifest['files']}
for n,b in data.items():assert len(b)==manifest['files'][n]['bytes'] and hashlib.sha256(b).hexdigest()==manifest['files'][n]['sha256']
for n,b in data.items():
    p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);p.chmod(manifest['files'][n]['mode'])
(root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
env={**os.environ,'LD_LIBRARY_PATH':str(root/'lib')}
p=subprocess.run(['ldd',str(root/'bin/rkaiq_3A_server')],env=env,capture_output=True,text=True,timeout=10)
assert p.returncode==0 and 'not found' not in p.stdout+p.stderr,(p.stdout,p.stderr)
links={}
for n in data:
    if not n.startswith('iqfiles/'):continue
    target=Path('/etc/iqfiles')/Path(n).name
    assert not target.exists() and not target.is_symlink(),str(target)
    target.parent.mkdir(parents=True,exist_ok=True);target.symlink_to(root/n);links[str(target)]=str(root/n)
print(json.dumps({'root':str(root),'dependency_check':p.stdout,'iq_links':links,'files':manifest['files'],
 'server_started':False,'autostart_installed':False,'global_libraries_replaced':False},indent=2))
PY
