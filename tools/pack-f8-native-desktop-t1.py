"""Build native writable ext4 and matching boot FIT, without flashing hardware."""
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import os
import stat
import struct
import subprocess
import sys
import uuid
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'tools'))
from inspect_images import fdt
root=Path('/var/tmp/f8-pro-armbian/desktop-t1/rootfs')
work=Path('/var/tmp/f8-pro-armbian/desktop-t1/native-image');work.mkdir(exist_ok=True)
out=P/'outputs/armbian/official-f8-desktop-t1'
assert (out/'desktop-native-validation.json').exists()
assert not (out/'native-image-manifest.json').exists(),'Preserve completed images'
# Pick up the final MAC-preserve fix; no private credentials are copied.
(root/'usr/libexec/f8-pro/native-prepare.sh').write_bytes((P/'armbian/desktop-t1/native-prepare.sh').read_bytes())
assert not list((root/'etc/ssh').glob('ssh_host_*_key'))
assert not list((root/'etc/NetworkManager/system-connections').glob('*'))
for fs in ['dev','proc','sys','run']:assert subprocess.run(['mountpoint','-q',str(root/fs)]).returncode!=0
identity=work/'root-uuid.txt'
if not identity.exists():identity.write_text(str(uuid.uuid4())+'\n')
root_uuid=identity.read_text().strip()
image=work/'ROOTFS_ARMBIAN_DESKTOP_T1.ext4.img'
if image.exists():
    assert '--resume-fsck-image' in sys.argv and image.stat().st_size==12*1024**3
    assert 'Pass 5:' in (out/'native-fsck.log').read_text()
    print('Resuming existing ext4 after completed mkfs; rechecking filesystem',flush=True)
else:
    with image.open('xb') as stream:stream.truncate(12*1024**3)
    print('Populating native 12GiB ext4 from verified desktop root',flush=True)
    with (out/'native-mkfs.log').open('w') as log:
        subprocess.run(['mkfs.ext4','-F','-L','F8_ARMBIAN','-U',root_uuid,'-O','^orphan_file',
          '-E','lazy_itable_init=0,lazy_journal_init=0','-d',str(root),str(image)],stdout=log,stderr=subprocess.STDOUT,check=True)
with (out/'native-fsck.log').open('w') as log:
    subprocess.run(['e2fsck','-fn',str(image)],stdout=log,stderr=subprocess.STDOUT,check=True)
print('Native filesystem created; hashing and packaging boot',flush=True)
fingerprint={'inode':image.stat().st_ino,'mtime_ns':image.stat().st_mtime_ns,'bytes':image.stat().st_size}
cache=work/'root-hash-cache.json'
if '--defer-root-hash' in sys.argv:
    root_sha=None
elif cache.exists() and json.loads(cache.read_text())['fingerprint']==fingerprint:
    root_sha=json.loads(cache.read_text())['sha256']
else:
    with image.open('rb') as stream:root_sha=hashlib.file_digest(stream,'sha256').hexdigest()
    cache.write_text(json.dumps({'fingerprint':fingerprint,'sha256':root_sha})+'\n')
r6=P/'outputs/armbian/official-f8-live-g6-r6';prior=json.loads((r6/'preflight.json').read_text())
blob=(r6/prior['candidate_file']).read_bytes();assert hashlib.sha256(blob).hexdigest()==prior['candidate_sha256']
fit=fdt(blob)
for name in ['kernel','fdt','ramdisk','resource']:
    prop=fit['/images/'+name];a=int.from_bytes(prop['data-position'],'big');size=int.from_bytes(prop['data-size'],'big')
    body=blob[a:a+size];assert hashlib.sha256(body).digest()==fit['/images/'+name+'/hash']['value']
    (work/name).write_bytes(body)
before=fdt((work/'fdt').read_bytes());expected=copy.deepcopy(before)
args=before['/chosen']['bootargs'].decode().rstrip('\0').split()
args=[s for s in args if not s.startswith(('root=','rootfstype=','rootflags=','systemd.unit=')) and s not in ['ro','rw']]
args+=['root=UUID='+root_uuid,'rootfstype=ext4','rw','systemd.unit=f8-desktop.target']
bootargs=' '.join(args)
model='F8-PRO official Armbian native Plasma Wayland desktop T1'
for node,key,value in [('/chosen','bootargs',bootargs),('/','model',model)]:
    subprocess.run(['fdtput','-t','s',str(work/'fdt'),node,key,value],check=True)
expected['/chosen']['bootargs']=bootargs.encode()+b'\0';expected['/']['model']=model.encode()+b'\0'
assert fdt((work/'fdt').read_bytes())==expected
spec=importlib.util.spec_from_file_location('cpio',P/'tools/build-usb-bootlog.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
records=helper.cpio_read(gzip.decompress((work/'ramdisk').read_bytes()))
fat=work/'logs.img'
with fat.open('wb') as stream:stream.truncate(16*1024**2)
subprocess.run(['mkfs.vfat','-n','F8ADT1',str(fat)],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['fsck.vfat','-n',str(fat)],check=True,stdout=subprocess.DEVNULL)
init=(P/'armbian/desktop-t1/native-init.sh.in').read_text().replace('@ROOT_UUID@',root_uuid).encode()
logger=(root/'usr/libexec/f8-pro/graphics-report').read_bytes()
new=[]
for name,values,body in records:
    if name.startswith(('f8-g3-assets','f8-live-firmware')) or name in ['f8-gpu-probe','f8-wayland-run','f8-wayland-client']:continue
    if name=='init':body=init
    elif name=='f8-evaluation-report':body=logger
    elif name=='f8-firstboot-logs.img':body=fat.read_bytes()
    fields=list(values);fields[6]=len(body);new.append((name,fields,body))
packed=helper.cpio_write(new);check={n:b for n,v,b in helper.cpio_read(packed)}
assert len(check)==len(new) and b'/run/f8/container' not in init and b'rootfs.squashfs' not in init
busybox=work/'busybox';busybox.write_bytes(check['bin/busybox']);busybox.chmod(0o755)
for name in ['init','f8-evaluation-report']:
    path=work/(name+'.sh');path.write_bytes(check[name])
    subprocess.run(['qemu-aarch64-static',str(busybox),'sh','-n',str(path)],check=True)
probe=work/'packed-blkid-runtime';probe.mkdir(exist_ok=True)
for name,values,body in new:
    if not (name in ['lib','lib64','sbin'] or name.startswith(('lib/','lib64/','sbin/'))):continue
    if '/modules' in name:continue
    dest=probe/name;kind=stat.S_IFMT(values[1])
    if kind==stat.S_IFDIR:dest.mkdir(parents=True,exist_ok=True)
    elif kind==stat.S_IFLNK:
        dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.is_symlink():dest.symlink_to(body.decode())
    elif kind==stat.S_IFREG:
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(body);dest.chmod(values[1]&0o777)
actual_uuid=subprocess.check_output(['qemu-aarch64-static','-L',str(probe),str(probe/'sbin/blkid'),'-s','UUID','-o','value',str(image)],text=True).strip()
assert actual_uuid==root_uuid
(work/'ramdisk').write_bytes(gzip.compress(packed,compresslevel=6,mtime=0))
its=Path('/var/tmp/f8-pro-armbian/official-live-g6-r6/boot.its').read_text().replace('G6 WIFI SSH LIVE','NATIVE DESKTOP T1')
(work/'boot.its').write_text(its)
boot=out/'BOOT_NATIVE_ARMBIAN_DESKTOP_T1.img'
(out/'native-mkimage.log').write_text(subprocess.check_output(['mkimage','-E','-p','0x800','-f','boot.its',str(boot)],cwd=work,text=True))
data=boot.read_bytes();tree=fdt(data);payloads={}
for name in ['kernel','fdt','ramdisk','resource']:
    prop=tree['/images/'+name];a=int.from_bytes(prop['data-position'],'big');size=int.from_bytes(prop['data-size'],'big')
    value=data[a:a+size];assert value==(work/name).read_bytes()
    digest=hashlib.sha256(value).digest();assert digest==tree['/images/'+name+'/hash']['value'];payloads[name]=digest.hex()
assert len(data)<64*1024**2
runtime=struct.unpack_from('<Q',(work/'kernel').read_bytes(),16)[0]
ranges=[(0x400000,0x400000+runtime),(0x8300000,0x8300000+(work/'fdt').stat().st_size+12288),
 (0xa200000,0xa200000+(work/'ramdisk').stat().st_size)]
memory=json.loads((P/'analysis/armbian/live-memory-baseline.json').read_text())
banks=[(int(b['base'],16),int(b['base'],16)+int(b['size'],16)) for b in memory['banks']]
for i,(a,b) in enumerate(ranges):
    assert any(x<=a<b<=y for x,y in banks)
    for j,(x,y) in enumerate(ranges):
        if i!=j:assert not(a<y and x<b)
record={'scope':'Native writable root partition plus matching boot, full Wayland desktop',
 'root_image':str(image),'root_bytes':image.stat().st_size,'root_sha256':root_sha,'root_sha256_pending':root_sha is None,'root_uuid':root_uuid,
 'boot_file':boot.name,'boot_bytes':len(data),'boot_sha256':hashlib.sha256(data).hexdigest(),
 'payload_sha256':payloads,'root_lba':'0x00078000','root_partition_sectors':482344960,
 'boot_lba':'0x00008000','boot_partition_sectors':131072,'partition_table_changes':False,
 'filesystem_writable':True,'contains_private_wifi_or_host_keys':False,
 'first_boot_auto_login':'f8test','first_boot_wifi_manual':True,'new_host_identity_first_boot':True,
 'real_desktop_hot_start_verified':True,'native_cold_boot_verified':False,'target_partition_written':False,
 'fsck_passed':True,'arm64_init_uuid_probe_passed':True,'fit_and_memory_layout_verified':True}
(out/'native-image-manifest.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2),flush=True)
