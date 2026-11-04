"""Verify signed official image; inspect its root filesystem read-only in WSL."""
import hashlib
import fcntl
import json
import lzma
from pathlib import Path
import re
import shutil
import struct
import subprocess
import time
import urllib.request
import zlib

P=Path('/mnt/d/Netdisk/Other/F8-PRO/archlinux')
evidence=P/'analysis/armbian/official-gpu-baseline-20261029'
record=json.loads((evidence/'downloaded-desktop.json').read_text())
archive=P/record['project_relative_path']
with archive.open('rb') as stream:
    assert hashlib.file_digest(stream,'sha256').hexdigest()==record['sha256']
work=Path('/var/tmp/f8-pro-armbian/official-desktop-26.8.1')
work.mkdir(exist_ok=True)
lock=(work/'inspection.lock').open('a')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
keydir=work/'signature-keyring';keydir.mkdir(exist_ok=True);keydir.chmod(0o700)
key=evidence/'image-signing-key.asc'
fingerprint='DF00FAF1C577104B50BF1D0093D6889F9F0E78D5'
if not key.exists():
    url='https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x'+fingerprint
    req=urllib.request.Request(url,headers={'User-Agent':'F8-PRO-Armbian-image-verification'})
    with urllib.request.urlopen(req,timeout=40) as response:key.write_bytes(response.read())
shown=subprocess.check_output(['gpg','--homedir',str(keydir),'--batch','--with-colons','--show-keys',str(key)],text=True)
assert fingerprint in shown
subprocess.run(['gpg','--homedir',str(keydir),'--batch','--import',str(key)],check=True,capture_output=True)
result=subprocess.run(['gpg','--homedir',str(keydir),'--batch','--status-fd','1','--verify',str(archive)+'.asc',str(archive)],capture_output=True,text=True)
(evidence/'signature-verification.log').write_text(result.stdout+result.stderr)
assert result.returncode==0 and 'VALIDSIG '+fingerprint in result.stdout
record['signature_verified']=True;record['signing_key_fingerprint']=fingerprint
(evidence/'downloaded-desktop.json').write_text(json.dumps(record,indent=2)+'\n')
image=work/'official.img'
if not image.exists():
    part=work/'official.img.part'
    # Replay and byte-check the existing prefix before extending interrupted output.
    # A mismatch preserves the file and aborts; no blind append or truncation.
    existing=part.stat().st_size if part.exists() else 0
    count=0;last=time.monotonic()
    with lzma.open(archive,'rb') as source,part.open('r+b' if existing else 'xb') as dest:
        while chunk:=source.read(4*1024*1024):
            overlap=min(len(chunk),max(0,existing-count))
            if overlap:assert dest.read(overlap)==chunk[:overlap], 'Interrupted prefix mismatch'
            if overlap<len(chunk):dest.write(chunk[overlap:])
            count+=len(chunk)
            if time.monotonic()-last>=20:
                print(json.dumps({'uncompressed_bytes_checked':count,'previous_prefix_bytes':existing}),flush=True)
                last=time.monotonic()
        assert count>=existing
    part.rename(image)
record['image_extracted']=True
(evidence/'downloaded-desktop.json').write_text(json.dumps(record,indent=2)+'\n')
print('Signature verified and official image decompressed',flush=True)
# Parse bounded GPT table with CRC checks; no device node is read or written.
with image.open('rb') as stream:
    stream.seek(512);header=bytearray(stream.read(512))
    assert header[:8]==b'EFI PART'
    header_size=struct.unpack_from('<I',header,12)[0];assert 92<=header_size<=512
    stored=struct.unpack_from('<I',header,16)[0];struct.pack_into('<I',header,16,0)
    assert zlib.crc32(header[:header_size])&0xffffffff==stored
    entry_lba=struct.unpack_from('<Q',header,72)[0]
    count,size,crc=struct.unpack_from('<III',header,80)
    assert 0<count<=4096 and 128<=size<=1024
    stream.seek(entry_lba*512);table=stream.read(count*size)
    assert zlib.crc32(table)&0xffffffff==crc
    partitions=[]
    for i in range(count):
        entry=table[i*size:(i+1)*size]
        if entry[:16]==bytes(16):continue
        start,end=struct.unpack_from('<QQ',entry,32)
        assert 0<start<=end and (end+1)*512<=image.stat().st_size
        stream.seek(start*512+1024+56)
        magic=stream.read(2)
        partitions.append({'number':i+1,'start_lba':start,'end_lba':end,
                           'name':entry[56:128].decode('utf-16-le').rstrip('\0'),
                           'ext_magic':magic.hex()})
root=next(x for x in partitions if x['ext_magic']=='53ef')
assert sum(x['ext_magic']=='53ef' for x in partitions)==1
mnt=work/'readonly-root';mnt.mkdir(exist_ok=True)
assert not subprocess.run(['mountpoint','-q',str(mnt)]).returncode==0
subprocess.run(['mount','-t','ext4','-o',f"ro,noload,loop,offset={root['start_lba']*512},sizelimit={(root['end_lba']-root['start_lba']+1)*512}",str(image),str(mnt)],check=True)
try:
    copies=['etc/armbian-release','etc/os-release','boot/armbianEnv.txt','etc/fstab',
            'var/lib/dpkg/status','etc/apt/sources.list','etc/apt/sources.list.d/armbian.sources']
    # Resolve absolute symlinks against the mounted target, never the host root.
    def target_path(relative):
        path=mnt/relative
        if path.is_symlink():
            link=path.readlink()
            path=mnt/str(link).lstrip('/') if link.is_absolute() else path.parent/link
        assert path.resolve().is_relative_to(mnt.resolve()),path
        return path
    for relative in copies:
        path=target_path(relative)
        if path.is_file():
            dest=evidence/'image-root'/relative;dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(path.read_bytes())
    configfiles=list((mnt/'boot').glob('config-*'))
    assert len(configfiles)==1
    config=configfiles[0].read_text()
    (evidence/'official-image-kernel.config').write_text(config)
    config_entries={line.split('=',1)[0]:line.split('=',1)[1] for line in config.splitlines() if line.startswith('CONFIG_') and '=' in line}
    modules=list((mnt/'usr/lib/modules').glob('*'))
    if not modules:modules=list((mnt/'lib/modules').glob('*'))
    firmware=list((mnt/'usr/lib/firmware').glob('arm/mali/**/mali_csffw.bin*'))
    if not firmware:firmware=list((mnt/'lib/firmware').glob('arm/mali/**/mali_csffw.bin*'))
    overlays=list((mnt/'boot').rglob('*panthor*.dtbo'))
    for f in overlays:
        dest=evidence/'image-overlays'/f.name;dest.parent.mkdir(exist_ok=True)
        dest.write_bytes(f.read_bytes())
        subprocess.run(['dtc','-I','dtb','-O','dts','-o',str(dest.with_suffix('.dts')),str(f)],check=True,capture_output=True)
    board_dtbs=list((mnt/'boot').glob('dtb-*/rockchip/rk3588s-orangepi-5.dtb'))
    gpu_nodes=[]
    if board_dtbs:
        import sys
        sys.path.insert(0,str(P/'tools'))
        from inspect_images import fdt
        for dtb in board_dtbs:
            data=dtb.read_bytes()
            (evidence/('official-'+dtb.name)).write_bytes(data)
            nodes=fdt(data)
            for path,props in nodes.items():
                if path.startswith('/gpu') and 'compatible' in props:
                    gpu_nodes.append({'dtb':dtb.name,'path':path,
                                      'compatible':props.get('compatible',b'').decode().replace('\0',','),
                                      'status':props.get('status',b'okay\0').decode().rstrip('\0')})
    status=(evidence/'image-root/var/lib/dpkg/status').read_text()
    packages=[]
    for block in status.split('\n\n'):
        fields=dict(line.split(': ',1) for line in block.splitlines() if ': ' in line and not line.startswith((' ','\t')))
        name=fields.get('Package','')
        if any(s in name for s in ['mesa','mali','panthor','firmware','kwin','plasma','sddm','armbian','linux-image','linux-dtb']):
            packages.append({k:fields.get(k) for k in ['Package','Version','Architecture','Status']})
    libmali=[x for x in (mnt/'usr/lib').rglob('*.so*') if x.name.lower().startswith('libmali')]
    report={'scope':'Official image mounted ro,noload locally; no target boot or maintainer scripts executed',
            'signature_verified':True,'image_bytes':image.stat().st_size,'partitions':partitions,
            'kernel_config':{k:config_entries.get('CONFIG_'+k,'n') for k in ['DRM_PANTHOR','DRM_PANFROST','MALI_MIDGARD','MALI_BIFROST','MALI_VALHALL','SQUASHFS','OVERLAY_FS']},
            'module_releases':[x.name for x in modules],
            'panthor_modules':[str(x.relative_to(mnt)) for m in modules for x in m.rglob('panthor.ko*')],
            'gpu_firmware':[{'path':str(x.relative_to(mnt)),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in firmware],
            'gpu_overlays':[str(x.relative_to(mnt)) for x in overlays],
            'gpu_nodes':gpu_nodes,
            'libmali_files':[str(x.relative_to(mnt)) for x in libmali],
            'packages':packages}
    (evidence/'official-image-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['packages']},indent=2),flush=True)
finally:
    subprocess.run(['umount',str(mnt)],check=True)
