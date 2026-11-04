"""Read bounded pstore evidence after the user restores the original BOOT."""
import base64
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

P=Path(__file__).resolve().parents[1]
out=P/'local/hardware/armbian-official-g1-failure-20261029-01'
assert not out.exists(),'Preserve previous capture; choose a new capture directory'
remote=r'''
import base64,json,os,subprocess
from pathlib import Path
assert os.uname().release=='5.10.160' and Path('/etc/arch-release').is_file()
records=[];total=0
for directory in ['/sys/fs/pstore','/var/lib/systemd/pstore']:
    root=Path(directory)
    if not root.is_dir():continue
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or not path.is_file():continue
        if not any(s in path.name.lower() for s in ['ramoops','dmesg','console','pstore']):continue
        if len(records)>=32:break
        size=path.stat().st_size
        if size>4*1024*1024:continue
        data=path.read_bytes();total+=len(data)
        if total>32*1024*1024:break
        records.append({'path':str(path),'mtime_ns':path.stat().st_mtime_ns,
                        'bytes':len(data),'base64':base64.b64encode(data).decode()})
def command(args):
    r=subprocess.run(args,capture_output=True,timeout=25)
    return {'exit_code':r.returncode,'stdout':r.stdout.decode(errors='replace'),
            'stderr':r.stderr.decode(errors='replace')}
result={'current_kernel':os.uname().release,'original_arch_confirmed':True,'records':records,
        'current_cmdline':Path('/proc/cmdline').read_text(),
        'pstore_mounts':[s for s in Path('/proc/mounts').read_text().splitlines() if 'pstore' in s],
        'current_dmesg':command(['dmesg']),
        'pstore_service_journal':command(['journalctl','-b','-u','systemd-pstore.service','--no-pager','-n','100'])}
print(json.dumps(result))
'''
prefix=['wsl','-d','rg35xx-build','-u','root','--','ssh',
 '-i','/var/tmp/f8-pro-archlinux-20261027/private-keys/f8-pro-test-ed25519',
 '-o','BatchMode=yes','-o','ConnectTimeout=8','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes',
 '-o','UserKnownHostsFile=/var/tmp/f8-pro-archlinux-20261027/test-known-hosts','alarm@192.168.1.227']
r=subprocess.run(prefix+['sudo -n python3 -c '+shlex.quote(remote)],capture_output=True,text=True,timeout=90)
assert r.returncode==0,r.stderr[-1000:]
result=json.loads(r.stdout);out.mkdir(parents=True)
files=[]
for i,record in enumerate(result.pop('records')):
    data=base64.b64decode(record.pop('base64'),validate=True)
    assert len(data)==record['bytes']
    name=f'pstore-{i:02d}.bin';(out/name).write_bytes(data)
    record.update(saved_file=name,sha256=hashlib.sha256(data).hexdigest())
    files.append(record)
    try:(out/f'pstore-{i:02d}.txt').write_text(data.decode('utf-8'),encoding='utf-8')
    except UnicodeDecodeError:pass
for field in ['current_dmesg','pstore_service_journal']:
    record=result.pop(field)
    (out/(field+'.txt')).write_text(record['stdout']+record['stderr'],encoding='utf-8')
    result[field+'_exit_code']=record['exit_code']
result.update(scope='Read-only recovery capture; current dmesg belongs to restored 5.10, not the failed candidate',
              user_report='G1 always black, no USB log disk; original BOOT restored',files=files)
(out/'capture.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'saved_directory':str(out),'original_arch_confirmed':True,'pstore_files':files},indent=2))
