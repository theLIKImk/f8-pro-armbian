"""Stream a consistent read-only original filesystem archive to private WSL storage."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
P=Path(__file__).resolve().parents[1]
private=Path('/var/tmp/f8-pro-armbian/private-backups/20261030-original-root')
private.mkdir(parents=True,exist_ok=True,mode=0o700);private.chmod(0o700)
archive=private/'original-rootfs.tar.gz';part=private/'original-rootfs.tar.gz.part'
manifest=private/'backup.json'
assert not archive.exists() and not part.exists() and not manifest.exists(),'Preserve existing backups'
base=Path('/var/tmp/f8-pro-archlinux-20261027')
ssh=['ssh','-T','-i',str(base/'private-keys/f8-pro-test-ed25519'),'-o','BatchMode=yes','-o','IdentitiesOnly=yes',
 '-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=192.168.1.227','-o','UserKnownHostsFile='+str(base/'test-known-hosts'),
 '-o','ServerAliveInterval=15','-o','ServerAliveCountMax=4','f8test@192.168.1.227']
probe="""python3 - <<'PY'
import json,os
from pathlib import Path
p=Path('/run/f8/container')
assert (p/'etc/arch-release').is_file()
line=next(s.split() for s in Path('/proc/mounts').read_text().splitlines() if s.split()[1]=='/run/f8/container')
assert line[0]=='/dev/mmcblk0p6' and 'ro' in line[3].split(',')
print(json.dumps({'read_only_container':True,'root_partition_start':int(Path('/sys/class/block/mmcblk0p6/start').read_text()),
 'root_partition_size':int(Path('/sys/class/block/mmcblk0p6/size').read_text())}))
PY"""
r=subprocess.run(ssh+['sudo -n sh -c '+__import__('shlex').quote(probe)],capture_output=True,text=True,timeout=30)
assert r.returncode==0,r.stderr[-500:];layout=json.loads(r.stdout)
assert layout['root_partition_start']==0x78000
command="sudo -n tar --xattrs --acls --numeric-owner --one-file-system --sparse -I 'gzip -1' -C /run/f8/container -cf - ."
checksum=hashlib.sha256();count=0;next_report=256*1024**2;started=time.monotonic()
with (private/'backup-stderr.log').open('wb') as errors:
    proc=subprocess.Popen(ssh+[command],stdout=subprocess.PIPE,stderr=errors)
    fd=os.open(part,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as stream:
        while True:
            chunk=proc.stdout.read(1024*1024)
            if not chunk:break
            stream.write(chunk);checksum.update(chunk);count+=len(chunk)
            if count>=next_report:
                print(json.dumps({'private_backup_received_mib':count//1024**2}),flush=True);next_report+=256*1024**2
        stream.flush();os.fsync(stream.fileno())
    code=proc.wait(timeout=30)
assert code==0,'Backup stream failed; preserve partial archive for diagnosis'
print('Verifying private backup compression and archive listing',flush=True)
subprocess.run(['gzip','-t',str(part)],check=True)
with (private/'archive-list.txt').open('w') as listing:
    subprocess.run(['tar','-tzf',str(part)],stdout=listing,check=True)
listing=(private/'archive-list.txt').read_text()
for required in ['./etc/arch-release','./etc/passwd','./etc/ssh/ssh_host_ed25519_key',
                 './var/lib/f8-pro/armbian-official-26.8.1/rootfs.squashfs']:
    assert required in listing,required
part.rename(archive)
record={'date':'2026-10-30','archive':str(archive),'bytes':count,'sha256':checksum.hexdigest(),
 'filesystem_snapshot_readonly':True,'gzip_crc_verified':True,'tar_listing_verified':True,
 'contains_private_wifi_ssh_and_user_data':True,'not_part_of_public_test_bundle':True,
 'layout':layout,'elapsed_seconds':time.monotonic()-started}
manifest.write_text(json.dumps(record,indent=2)+'\n');manifest.chmod(0o600)
summary=P/'local/hardware/armbian-desktop-t1-live-20261030-01/original-backup-manifest.json'
summary.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'private_backup_complete':True,'bytes':count,'sha256':record['sha256']}),flush=True)
